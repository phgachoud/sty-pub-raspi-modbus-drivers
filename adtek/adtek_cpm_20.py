#!/usr/bin/env python3
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#       DESCRIPTION: 
#			https://github.com/riptideio/pymodbus
#
#       CALL SAMPLE:
#                sudo /home/pg/data/solarity/sit-raspi/current_monitoring/rs485_to_usb/adtek_cpm_20_v2.py --channel 1 --host_ip 172.16.10.139 --host_mac b8:27:eb:b0:36:2f -v --store_values
#       CALL PARAMETERS:
#               1) 
#	REQUIRE
#		sudo apt-get install python-pygments python-pip python-pymodbus python3-pip
#		sudo pip3 install -U pymodbus
#		sudo pip3 install click
#		sudo pip3 install requests
#		sudo pip3 install prompt_toolkit --upgrade
#		sudo pip install -U pymodbus click requests prompt_toolkit 
#
#		**** PYTHON 3 *****
#		sudo apt install python3-pip
#		sudo pip3 install requests click pymodbus prompt_toolkit
#
#       @author: Philippe Gachoud
#       @creation: 20190421
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# INCLUDES
try:
	import sys
	import os.path
	import os, errno
	import logging # http://www.onlamp.com/pub/a/python/2005/06/02/logging.html
	from logging import handlers
	import csv
	import socket
	import pymodbus
	import serial
	from pymodbus.pdu import ModbusRequest
	from pymodbus.client.sync import ModbusSerialClient as ModbusClient #initialize a serial RTU client instance https://github.com/riptideio/pymodbus/blob/master/pymodbus/client/sync.py
	#from pymodbus.client.sync import ModbusTcpClient as ModbusClient # FOR TCP
	from pymodbus.transaction import ModbusRtuFramer
	import time
	import requests
	import argparse
	from datetime import datetime
	import struct
	import json  #for pretty printing in log

	from pymodbus.payload import BinaryPayloadBuilder
	from pymodbus.constants import Endian
	from pymodbus.payload import BinaryPayloadDecoder
	from collections import OrderedDict

	#sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) + '/DLSS/dlss_libs/')
except ImportError as l_err:
	print("ImportError: {0}".format(l_err))
	raise l_err

class AdtekCpm20:

# CONSTANTS
	DEFAULT_LOGGING_LEVEL=logging.DEBUG #For console overrided by --verbose
	DEFAULT_FILE_LOGGING_LEVEL=logging.DEBUG #For file
	DEFAULT_BASE_URL="http://localhost:9999/" # with ending slash
	DEFAULT_PORT="/dev/ttyUSB0" #https://unix.stackexchange.com/a/144735/47775 to get it
	DEFAULT_METHOD="rtu"

	LOG_FILE_PATH = '/var/log/solarity'
	DEFAULT_CSV_FILE_LOCATION = '/var/solarity' #without ending slash

# VARIABLES
	__logger = None
	__console_handler = None
	__file_handler = None

	__modbus_client = None
	__is_connected = False
	__base_url = DEFAULT_BASE_URL

# FUNCTIONS DEFINITION 

	def __init__(self):
		"""
		Initialize
		"""
		try:
			if not os.path.isdir(self.LOG_FILE_PATH):
				l_msg = 'log file path not found, check if it has been created -%s-' % self.LOG_FILE_PATH
				print(l_msg)
				exit(1)
			#*** Logger
			fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
			self.__logger = logging.getLogger(__name__) 
			#self.__logger.propagate = False
			self.__logger.setLevel(logging.DEBUG)
			self.__console_handler = logging.StreamHandler(sys.stdout)
			self.__console_handler.setFormatter(fmt)
			self.__console_handler.setLevel(self.DEFAULT_LOGGING_LEVEL)

			self.__file_handler = handlers.RotatingFileHandler("{0}/{1}.log".format(self.LOG_FILE_PATH, os.path.basename(__file__)), maxBytes=1048576, backupCount=10)
			self.__file_handler.setFormatter(fmt)
			self.__file_handler.setLevel(self.DEFAULT_FILE_LOGGING_LEVEL)

			self.__logger.addHandler(self.__file_handler)
			self.__logger.addHandler(self.__console_handler)
			#pymodbus
			l_log = logging.getLogger('pymodbus.protocol')
			l_log.setLevel(logging.DEBUG)
		except Exception as l_e:
			print('Error in init: %s' % (l_e))
			exit(1)

	def process_script_arguments(self):
		"""
		reads script arguments and executes corresponding argument
		"""
		self.init_arg_parse()
		self.connect()
		self.execute_corresponding_args()

	def connect(self):
		"""
		sets self.__modbus_client and connects to it
		"""
		assert not self.is_connected()
		try:
			#self.__register_value
			#count= the number of registers to read
			#unit= the slave unit this request is targeting
			#address= the starting address to read from

			self.__modbus_client = ModbusClient(method="rtu", port="/dev/ttyUSB0", timeout=1, stopbits=1, bytesize=8, parity='N', baudrate=9600)
			self.__logger.debug("IP:%s" % self.__args)
			#self.__modbus_client = ModbusClient(self.__args.host_ip, retries=3, retry_on_empty=True)
			#self.__modbus_client = ModbusClient('172.16.10.139', port=502, retry_on_empty=True)

			#Connect to the serial modbus server
			connection = self.__modbus_client.connect()
			if self.__modbus_client.connect:
				#self.__logger.debug("Client is connected")
				self.__is_connected = True
			else:
				raise Exception("Could not connect to __modbus_client")
		except Exception as l_e:
			self.__logger.exception("connect:Exception occured during connection" + l_e.message)
			raise l_e

	def register_value(self, a_register_index, a_register_length):
		"""
		Returns a given register value
		@a_register_length: 1 register is 16 bits (2 bytes = 1 word)
		"""
		assert self.__args.channel, "channel is empty"
		assert self.is_connected(), "register_value->device is not connected"
		try:

			#Starting add, num of reg to read, slave unit.
			l_result = self.__modbus_client.read_holding_registers(a_register_index, a_register_length, unit=int(self.__args.channel)) # Average current
			if l_result is not None:
				self.__logger.debug(l_result.__str__())
				if l_result.function_code < 0xFFFFFFFF:
					self.__logger.debug("register_value->registers:%s" % l_result.registers)
					#self.__logger.debug(l_result)
					#self.__logger.debug("register_value->register 0 value:%s" % l_result.getRegister(1))
					self.__logger.debug("register 0 type:%s" % type(l_result.getRegister(0)))
					#self.__logger.debug(l_result.__str__())
				else:
					self.__logger.error("register_value-> returned code is invalid: %s" % l_result.function_code)
			else:
				self.__logger.error("register_value-> No register received, l_result is None")

		except KeyboardInterrupt:
			self.__logger.exception("Keyboard interruption")
		except Exception as l_e:
			self.__logger.exception("register:Exception occured, msg:" + l_e.message)
		finally:
#			self.__logger.info("register:".join(str(e) for e in result))
			return l_result

	def register_value_invalid_int(self, a_register_index, a_register_length):
		"""
		Returns a given register value
		@a_register_length: 1 register is 16 bits (2 bytes = 1 word)
		"""
		assert self.__args.channel, "channel is empty"
		assert self.is_connected(), "register_value->device is not connected"
		try:

			#https://groups.google.com/forum/#!topic/pymodbus/X4vtEg9Hq10
			#https://stackoverflow.com/questions/32421197/struct-error-required-argument-is-not-an-integer
			# FLOAT32	Floating Point, 32 bits	+/- 1*10^38	0xFFC00000
			#	PYTHON DOC: https://docs.python.org/2/library/struct.html#format-characters
			#
			#self.__modbus_client.read_holding_registers(a_register_index => /home/pg/data/solarity/sit-raspi/current_monitoring/rs485_to_usb/schneider_pm5500.py
			
				

			#Starting add, num of reg to read, slave unit.
			self.__logger.debug("register_value_invalid_int->about to read register index:%s length:%s channel:%s" % (a_register_index, a_register_length, self.__args.channel))
			l_result = self.__modbus_client.read_holding_registers(a_register_index, a_register_length, unit=int(self.__args.channel)) # Average current
			if l_result is not None:
				self.__logger.debug(l_result.__str__())
				if l_result.function_code < 0xFFFFFFFF:
					self.__logger.debug("register_value->registers:%s" % l_result.registers)
					#self.__logger.debug(l_result)
					#self.__logger.debug("register_value->register 0 value:%s" % l_result.getRegister(1))
					self.__logger.debug("register 0 type:%s" % type(l_result.getRegister(0)))
					#self.__logger.debug(l_result.__str__())
				else:
					self.__logger.error("register_value-> returned code is invalid: %s" % l_result.function_code)
			else:
				self.__logger.error("register_value-> No register received, l_result is None")

		except KeyboardInterrupt:
			self.__logger.exception("Keyboard interruption")
		except Exception as l_e:
			self.__logger.exception("register:Exception occured, msg:" + l_e.message)
		finally:
#			self.__logger.info("register:".join(str(e) for e in result))
			return l_result

	def get_csv_file_path(self):
		"""
		Returns the csv file path
		"""
		assert self.__args.host_ip, "host ip is empty"
		assert self.__args.channel, "channel is empty"
		assert self.__args.host_mac, "host mac is empty"
		if __debug__:
			try:
				socket.inet_aton(self.__args.host_ip)
			except socket.error as l_e:
				assert False, "Host ip address is invalid"
				raise l_e

		l_dir = self.DEFAULT_CSV_FILE_LOCATION + '/' + str(datetime.today().year) + '/' + str(datetime.today().month)
		l_result = (l_dir + '/' +
			datetime.today().strftime('%Y%m%d') + '_' + 
			self.__args.host_mac.replace(':', '-') + '_' + 
			self.__args.host_ip + '_' + 
			self.__args.channel + '_' + 
			os.path.basename(__file__) + '.csv')

		try:
			os.makedirs(l_dir)
		except OSError as l_e:
			if l_e.errno == errno.EEXIST:
				pass
			else:
				self.__logger.error('get_csv_file_path Error: %s' % (l_e))
				raise

		return l_result


	def post_to_sit_platform(self, a_values_dictionnary):
		"""
		Posts given values disctionnary to solarity platform
		"""
		assert self.is_connected()

		self.update_dict_values_with_registers(a_values_dictionnary)
		self.update_dict_values_with_arguments(a_values_dictionnary)
		l_url = self.service_url(a_values_dictionnary)
		self.set_json_data(a_values_dictionnary)

		if self.__args.display_only:
			self.__logger.info("Charge read value is:%s" % a_values_dictionnary['charge'])
		else:
			try:
				self.__logger.debug("now posting... '%s'" % (a_values_dictionnary['json']))
				l_request_result = requests.post(l_url, json=a_values_dictionnary['json'], timeout=30)
				if l_request_result.status_code == 200:
					self.__logger.info("posting to %s, values:%s" % (l_url, a_values_dictionnary['json']) + " Result from post is %s" % l_request_result)
				else:
					self.__logger.error("posting to %s, values:%s" % (l_url, a_values_dictionnary['json']) + " Result from post is %s" % l_request_result)
			except Exception as l_e:
				self.__logger.error("Got an exception trying to post data %s" % a_values_dictionnary['json'], l_e)
				raise l_e


	def set_json_data(self, a_values_dictionnary):
		"""
		Sets json data
		"""
		if a_values_dictionnary['sit_platform_object_type'] == 'charge_unit':
			assert a_values_dictionnary['charge'] is not None
			assert a_values_dictionnary['timestamp'] is not None
			assert a_values_dictionnary.has_key('measuring_point_id') and int(a_values_dictionnary['measuring_point_id']) > 0, "Please provide a valid measuring_point_id"
			a_values_dictionnary['json'] = { 
				'name': "hostname=" + socket.gethostname(),
				'charge': a_values_dictionnary['charge'],
				'timestamp': a_values_dictionnary['timestamp'],
				'measuring_point': { 'id':int(a_values_dictionnary['measuring_point_id']) }
			}
		elif a_values_dictionnary['sit_platform_object_type'] == 'power_factor':
			raise Exception("values_dictionnary_to_json not treated data type")
		else:
			raise Exception("values_dictionnary_to_json not treated data type")
		assert a_values_dictionnary['json'] is not None

	def service_url(self, a_values_dictionnary):
		"""
		Returns web service URL with object_type
		"""
		assert a_values_dictionnary.has_key('sit_platform_object_type')
		assert self.__base_url.endswith("/")

		result = self.__base_url + a_values_dictionnary['sit_platform_object_type'] 

		return result

	def get_csv_row(self):
		"""
		@returns an array with a row to store into csv corresponding to self.CSV_HEADER_ROW
		"""
		self.__logger.info("-->IP:%s MAC:%s" % (self.__args.host_ip, self.__args.host_mac))	
		l_result = OrderedDict() #https://groups.google.com/forum/#!topic/pymodbus/X4vtEg9Hq10

		try:
			l_result['Timestamp'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
			l_result['F'] = '{:.3f}'.format(self.register_values_u_long(0x0) / 100) #Frequency
			l_result['V'] = '{:.2f}'.format(self.register_values_u_long(0x2) / 10) #Average phase voltage
			l_result['Iavg'] = '{:.4f}'.format(self.register_values_u_long(0x6) / 1000) #Average current
			l_result['In'] = '{:.4f}'.format(self.register_values_u_long(0x8) / 1000) #Neutral current
			l_result['P'] = '{:.4f}'.format(self.register_values_s_long(0xA) / 1000) #Total active power W => KW
			l_result['Q'] = self.register_values_s_long(0xC) #Total reactive power VAR => kVAR
			l_result['S'] = self.register_values_s_long(0xE) #Total apparent power VA => kVA
			l_result['PF'] = '{:.4f}'.format(self.register_values_s_long(0x10) / 1000) #Power factor average
			l_result['Ea'] = '{:.2f}'.format(self.register_values_u_long(0x12) / 10) #Active nrj
			l_result['Er'] = '{:.2f}'.format(self.register_values_u_long(0x14) / 10) #Reactive nrj
			l_result['V1'] = '{:.2f}'.format(self.register_values_u_long(0x1A) / 10) #P1 voltage
			l_result['V2'] = '{:.2f}'.format(self.register_values_u_long(0x1C) / 10) #
			l_result['V3'] = '{:.2f}'.format(self.register_values_u_long(0x1E) / 10) #
			l_result['U12'] = '{:.2f}'.format(self.register_values_u_long(0x20) / 10) #
			l_result['U23'] = '{:.2f}'.format(self.register_values_u_long(0x22) / 10) #
			l_result['U31'] = '{:.2f}'.format(self.register_values_u_long(0x24) / 10) #
			l_result['I1'] = '{:.4f}'.format(self.register_values_u_long(0x26) / 1000) # Amps
			l_result['I2'] = '{:.4f}'.format(self.register_values_u_long(0x28) / 1000) # Amps
			l_result['I3'] = '{:.4f}'.format(self.register_values_u_long(0x2A) / 1000) # Amps

			l_result['P1'] = '{:.4f}'.format(self.register_values_s_long(0x2C) / 1000) #Phase 1 active power W => KW
			l_result['P2'] = '{:.4f}'.format(self.register_values_s_long(0x2E) / 1000) #Phase 1 active power W => KW
			l_result['P3'] = '{:.4f}'.format(self.register_values_s_long(0x30) / 1000) #Phase 1 active power W => KW
			l_result['Q1'] = self.register_values_s_long(0x32) # Phase 1 reactive power W
			l_result['Q2'] = self.register_values_s_long(0x34) #
			l_result['Q3'] = self.register_values_s_long(0x36) #
			l_result['S1'] = self.register_values_s_long(0x38) # Phase 1 apparent power VA
			l_result['S2'] = self.register_values_s_long(0x3A) #
			l_result['S3'] = self.register_values_s_long(0x3C) #
			l_result['PF1'] = '{:.4f}'.format(self.register_values_s_long(0x3E) / 1000) #Power factor Line 1
			l_result['PF2'] = '{:.4f}'.format(self.register_values_s_long(0x40) / 1000) #
			l_result['PF3'] = '{:.4f}'.format(self.register_values_s_long(0x42) / 1000) #

			l_result['ThdU1'] = '{:.1f}'.format(self.register_values_u_word(0x45) / 10) #Phase A voltage total harmonic
			l_result['ThdU2'] = '{:.1f}'.format(self.register_values_u_word(0x46) / 10) #
			l_result['ThdU3'] = '{:.1f}'.format(self.register_values_u_word(0x47) / 10) #
			l_result['ThdU'] = '{:.1f}'.format(self.register_values_u_word(0x48) / 10) #
			l_result['ThdI1'] = '{:.1f}'.format(self.register_values_u_word(0x49) / 10) #Phase A current total harmonic
			l_result['ThdI2'] = '{:.1f}'.format(self.register_values_u_word(0x4A) / 10) #
			l_result['ThdI3'] = '{:.1f}'.format(self.register_values_u_word(0x4B) / 10) #
			l_result['ThdIn'] = '{:.1f}'.format(self.register_values_u_word(0x4C) / 10) #

			l_result['PTPri'] = self.register_values_s_long(0x4E) # PT Primary side voltage setting V
			l_result['PTSec'] = self.register_values_u_word(0x50) # PT Secondary voltage settings
			l_result['PTPri'] = self.register_values_u_word(0x51) # CT Primary current settings

			self.__logger.info("get_csv_row: %s" % ', '.join(['{}:{}'.format(k,v) for k,v in l_result.items()]))
			self.__logger.info("get_csv_row: %s" % json.dumps(l_result, indent=4))

			return l_result
		except Exception as l_e:
			self.__logger.exception("get_csv_row->Exception occured: %s" % (l_e))
			self.__logger.error('get_csv_row->Error: %s' % (l_e))
			raise l_e

	def _int_from_register(self, a_register, a_start_index, a_bits_count):
		"""
		"""
		l_tmp_binary = "{0:b}".format(a_register)
		l_tmp_binary = l_tmp_binary.zfill(16)
		l_end_index = len(l_tmp_binary) - a_start_index
		l_start_index = len(l_tmp_binary) - a_start_index - a_bits_count
		l_tmp = l_tmp_binary[l_start_index:l_end_index + 1] # second is where ends exclusive, first is inclusive
		l_result = int(l_tmp, 2)
		self.__logger.debug("************************************* _int_from_register-> register(%s) binary (%s) %s:%s => %s result(%s)" % (a_register, l_tmp_binary, l_start_index, l_end_index, l_tmp, l_result))
		return l_result

	def register_values_date_time(self, a_register_index):
		"""
		from spec returns a string formated 
		@a_register_index: a register index
		"""
		try:
			l_register_res = self.register_value_invalid_int(a_register_index, 4)
			self.__logger.debug("******* BEGIN ****************************** register_values_date_time->a_register_index:%s" % (a_register_index))
			l_year = self._int_from_register(l_register_res.registers[0], 0, 6) + 2000
			l_day = self._int_from_register(l_register_res.registers[1], 0, 4)
			l_month = self._int_from_register(l_register_res.registers[1], 8, 4)
			l_min = self._int_from_register(l_register_res.registers[2], 0, 5)
			l_hour = self._int_from_register(l_register_res.registers[2], 8, 5)
			l_sec = int(int(l_register_res.registers[3]) / 1000)


			l_result = str(l_year) + '-' + str(l_month).zfill(2) + '-' + str(l_day).zfill(2) + 'T' + str(l_hour).zfill(2) + ':' + str(l_min).zfill(2) + ':' + str(l_sec).zfill(2) + 'Z' #Definitive result as expecte
		except Exception as l_e:
			self.__logger.exception("register_values_date_time exception: %s" % l_e)
			raise l_e

		l_result = (';'.join(str(l) for l in l_register_res.registers)) # only decimals
		self.__logger.debug("******** END ***************************** register_values_date_time->registers:%s- result:%s-" % (l_register_res.registers, l_result))
		return l_result

	def register_values_pm5500_date_time(self, a_register_index):
		"""
		from spec returns a string formated with datetime
		@a_register_index: a register index start index, the followings will be read
		"""
		l_i = 0
		l_register_res = self.register_value_invalid_int(a_register_index + l_i, 1)
		l_year = l_register_res.registers[0]
		l_i = l_i + 1
		l_register_res = self.register_value_invalid_int(a_register_index + l_i, 1)
		l_month = l_register_res.registers[0]
		l_i = l_i + 1
		l_register_res = self.register_value_invalid_int(a_register_index + l_i, 1)
		l_day = l_register_res.registers[0]
		l_i = l_i + 1
		l_register_res = self.register_value_invalid_int(a_register_index + l_i, 1)
		l_hour = l_register_res.registers[0]
		l_i = l_i + 1
		l_register_res = self.register_value_invalid_int(a_register_index + l_i, 1)
		l_min = l_register_res.registers[0]
		l_i = l_i + 1
		l_register_res = self.register_value_invalid_int(a_register_index + l_i, 1)
		l_sec = l_register_res.registers[0]
		l_i = l_i + 1

		l_result = str(l_year) + str(l_month).zfill(2) + str(l_day).zfill(2) + 'T' + str(l_hour).zfill(2) + str(l_min).zfill(2) + str(l_sec).zfill(2) + 'Z'

		self.__logger.debug("register_values_pm5500_date_time->result:%s" % l_result)
		return l_result
		
	def register_values_float_32(self, a_register_index):
		"""
		from spec returns a float from given register index
		@a_register_index: a register index
		"""
		l_register_res = self.register_value_invalid_int(a_register_index, 2)
		#self.__logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		l_result = decoder.decode_32bit_float()
		self.__logger.debug("register_values_float_32->after decoder:%s" % l_result)
		return l_result

	def register_values_float_32_pf(self, a_register_index):
		"""
		from spec returns a float from given register index
		@a_register_index: a register index
			********* FROM DOC ***********************
			Power factor values are specially encoded floating point values.


			Pseudo code to decode PF Value
			if (rigVal > 1)
			{
			 PF_Val = 2 - regVal;
			  PF is leading
			  }
			  else if (regVal < -1)
			  {
			   PF_Val = -2-regVal
				PF is leading
				}
				else if ( abs(regVal) equals 1 )
				{
				 PF_Val = regVal
				  PF is at unity
				  }
				  else
				  {
				   PF_Val = regVal
					PF is lagging
					}

		"""
		l_register_res = self.register_value(a_register_index, 2)
		#self.__logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		l_result = decoder.decode_32bit_float()
		if l_result > 1:
			l_result = 2 - l_result
		elif l_result < -1: 
			l_result = -2 - l_result
		else:
			pass
		self.__logger.debug("register_values_float_32_pf->after decoder:%s" % l_result)
		return l_result

	def register_values_u_word(self, a_register_index):
		"""
		from spec returns a word from given register index
		@a_register_index: a register index
		"""
		l_register_res = self.register_value(a_register_index, 1)
		#self.__logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		l_result = decoder.decode_16bit_uint()
		self.__logger.debug("register_values_u_word->after decoder:%s" % l_result)
		return l_result

	def register_values_s_long(self, a_register_index):
		"""
		from spec returns a long from given register index
		@a_register_index: a register index
		"""
		l_register_res = self.register_value(a_register_index, 2)
		#self.__logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		l_result = decoder.decode_32bit_int()
		self.__logger.debug("register_values_s_long->after decoder:%s" % l_result)
		return l_result

	def register_values_u_long(self, a_register_index):
		"""
		from spec returns a long from given register index
		@a_register_index: a register index
		"""
		l_register_res = self.register_value(a_register_index, 2)
		#self.__logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		l_result = decoder.decode_32bit_uint()
		self.__logger.debug("register_values_u_long->after decoder:%s" % l_result)
		return l_result
	
	def register_values_int16_u(self, a_register_index):
		"""
		from spec returns an int
		@a_register_index: a register index
		"""
		l_register_res = self.register_value(a_register_index, 1)
		#self.__logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		l_result = decoder.decode_16bit_uint()
		self.__logger.debug("register_values_u_long->after decoder:%s" % l_result)
		return l_result

	def store_values_into_csv(self, a_row_dict):
		"""
		Stores values into CSV DEFAULT_CSV_FILE_LOCATION
		@param a_row_dict: a dictionnary as row 
		"""
		try:
			l_f_name = self.get_csv_file_path()
			l_file_exists = os.path.isfile(l_f_name)
			self.__logger.info("store_values_into_csv->Writting into file %s exists:%s" % (l_f_name, l_file_exists))
			with open(l_f_name, mode='a+') as l_csv_file:
				l_csv_writter = csv.writer(l_csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
				if not l_file_exists:
					self.__logger.info("store_values_into_csv->Writting HEADER row: %s" % (';'.join(str(l) for l in a_row_dict.keys())))
					l_csv_writter.writerow(a_row_dict.keys())
				self.__logger.info("store_values_into_csv->HEADER row: %s" % (';'.join(str(l) for l in a_row_dict.keys())))
				self.__logger.info("store_values_into_csv->Writting row: %s" % (';'.join(str(l) for l in a_row_dict.values())))
				l_csv_writter.writerow(a_row_dict.values())
		except Exception as l_e:
			self.__logger.error('store_values_into_csv->Error: %s' % l_e)
			print(l_e)
			sys.exit(1)
		finally:
			if self.is_connected():
				self.disconnect()
		
	"""
	Self explaining
	"""
	def is_connected(self):
		#self.__logger.debug("is_connected-> %s, modbusclient:%s" % (self.__is_connected, self.__modbus_client))
		return self.__modbus_client is not None and self.__is_connected

	"""
	Disconnects modbus client
	"""
	def disconnect(self):
		assert self.is_connected()
		assert self.__modbus_client is not None

		try:
			self.__modbus_client.close()
			self.__logger.debug("disconnecting")
			self.__is_connected = False
		except Exception as l_e:
			self.__logger.exception("disconnect->Exception occured msg:" + l_e.message)
			raise l_e

	"""
	Parsing arguments
	"""
	def init_arg_parse(self):
		self.__parser = argparse.ArgumentParser(description='Actions with Legrand power meter 14671')
		self.__parser.add_argument('-v', '--verbose', help='increase output verbosity', action="store_true")
		self.__parser.add_argument('-s', '--store_values', help='Store values into csv file', action="store_true")
		self.__parser.add_argument('-d', '--display_only', help='Only display read value, doesnt do the associated action (as logger INFO level)', action="store_true")
		self.__parser.add_argument('-t', '--test', help='Calls test method', action="store_true")
		self.__parser.add_argument('-u', '--base_url', help='Gives the base URL for requests actions', nargs='?', default=self.DEFAULT_BASE_URL)
		l_required_named = self.__parser.add_argument_group('required named arguments')
		l_required_named.add_argument('-c', '--channel', help='Channel index', nargs='?', required=True)
		l_required_named.add_argument('-i', '--host_ip', help='Host IP', nargs='?', required=True)
		l_required_named.add_argument('-m', '--host_mac', help='Host MAC', nargs='?', required=True)
		args = self.__parser.parse_args()
		self.__args = args

	"""
	Calls the corresponding function to given script argument
	"""
	def execute_corresponding_args( self ):
		if self.__args.verbose:
			self.__logger.setLevel(logging.DEBUG)
			self.__console_handler.setLevel(logging.DEBUG)
			self.__file_handler.setLevel(logging.DEBUG)
		else:
			self.__logger.setLevel(logging.DEBUG)
			self.__console_handler.setLevel(logging.ERROR)
			self.__file_handler.setLevel(logging.DEBUG)
			
		if self.__args.base_url:
			self.__logger.debug("execute_corresponding_args->given argument was '%s'" % self.__args.base_url)
			self.__base_url = self.__args.base_url
		if self.__args.store_values:
			self.store_values_into_csv(self.get_csv_row())
		if self.__args.test:
			self.test()

	"""
	Test method
	"""
	def test( self ):
		self.__logger.info("Test method->")

def main():
	""" """
	logger = logging.getLogger(__name__)
	l_o = AdtekCpm20()
	try:
		l_o.process_script_arguments()
	except Exception as l_e:
		logger.exception("disconnect:Exception occured msg:" + l_e.message)
		raise l_e
	finally:
		if l_o.is_connected():
			l_o.disconnect()



if __name__ == '__main__':
    main()