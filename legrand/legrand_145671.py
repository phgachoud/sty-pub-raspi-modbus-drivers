#!/usr/bin/env python
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#       DESCRIPTION: Operations with legrand 145671, see --help for more details
#
#       CALL SAMPLE:
#               Usage  ~/data/solarity/sit-raspi/sty-pub-raspi-modbus-drivers/legrand/legrand_145671.py
#
#	REQUIRE
#		sudo apt-get install python-pygments python-pip python-pymodbus python3-pip
#		sudo pip3 install requests click pymodbus prompt_toolkit
#
#		TODO: unify with sit_modbus_device
#
#	REQUIRE
#		**** PYTHON 3 *****
#		sudo apt install python3-pip
#		sudo pip3 install requests click pymodbus prompt_toolkit
#
#
#		*************************************************************************************************
#       @author: Philippe Gachoud
#       @creation: 20181121
#       @last modification:
#       @version: 1.0
#       @URL: $URL
#		*************************************************************************************************
#		Copyright (C) 2020 Solarity spa
#
#		This library is free software; you can redistribute it and/or
#		modify it under the terms of the GNU Lesser General Public
#		License as published by the Free Software Foundation; either
#		version 2.1 of the License, or (at your option) any later version.
#
#		This library is distributed in the hope that it will be useful,
#		but WITHOUT ANY WARRANTY; without even the implied warranty of
#		MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#		Lesser General Public License for more details.
#
#		You should have received a copy of the GNU Lesser General Public
#		License along with this library; if not, write to the Free Software
#		Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#		*************************************************************************************************
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
	from pymodbus.transaction import ModbusRtuFramer
	import time
	import requests
	import argparse
	from datetime import datetime
	import struct

	from pymodbus.payload import BinaryPayloadBuilder
	from pymodbus.constants import Endian
	from pymodbus.payload import BinaryPayloadDecoder
	from collections import OrderedDict

	#sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) + '/DLSS/dlss_libs/')
except ImportError as l_err:
	print("ImportError: {0}".format(l_err))
	raise l_err

class Legrand145671:

# CONSTANTS
	DEFAULT_LOGGING_LEVEL=logging.ERROR #For console overrided by --verbose
	DEFAULT_FILE_LOGGING_LEVEL=logging.DEBUG #For file
	DEFAULT_BASE_URL="http://localhost:9999/" # with ending slash
	DEFAULT_PORT="/dev/ttyUSB0" #https://unix.stackexchange.com/a/144735/47775 to get it
	SLAVE_UNIT_NUMBER=0xa # index of slave unit on the line: 10
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

	"""
	Initialize
	"""
	def __init__(self):
		try:
			if not os.path.isdir(self.LOG_FILE_PATH):
				l_msg = 'log file path not found, check if it has been created -%s-' % self.LOG_FILE_PATH
				print(l_msg)
				exit(1)
			#*** Logger
			fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
			self.__logger = logging.getLogger(__name__) 
			self.__logger.propagate = False
			self.__logger.setLevel(logging.DEBUG)
			self.__console_handler = logging.StreamHandler(sys.stdout)
			self.__console_handler.setFormatter(fmt)
			self.__console_handler.setLevel(self.DEFAULT_LOGGING_LEVEL)

			self.__file_handler = handlers.RotatingFileHandler("{0}/{1}.log".format(self.LOG_FILE_PATH, os.path.basename(__file__)), maxBytes=1024, backupCount=10)
			self.__file_handler.setFormatter(fmt)
			self.__file_handler.setLevel(self.DEFAULT_FILE_LOGGING_LEVEL)

			self.__logger.addHandler(self.__file_handler)
			self.__logger.addHandler(self.__console_handler)
		except Exception as l_e:
			print('Error in init: %s' % (l_e))
			exit(1)

	"""
	reads script arguments and executes corresponding argument
	"""
	def process_script_arguments(self):
		self.init_arg_parse()
		self.execute_corresponding_args()

	"""
	sets self.__modbus_client and connects to it
	"""
	def connect(self):
		assert not self.is_connected()
		try:
			#self.__register_value
			#count= the number of registers to read
			#unit= the slave unit this request is targeting
			#address= the starting address to read from

			self.__modbus_client = ModbusClient(method="rtu", port="/dev/ttyUSB0", stopbits=1, bytesize=8, parity='N', baudrate=9600)

			#Connect to the serial modbus server
			connection = self.__modbus_client.connect()
			if self.__modbus_client.connect:
				self.__logger.debug("Client is connected")
				self.__is_connected = True
			else:
				raise Exception("Could not connect to __modbus_client")
		except Exception as l_e:
			self.__logger.exception("connect:Exception occured during connection" + l_e.message)
			raise l_e

	"""
	Returns a given register value
	@a_register_length: 1 register is 16 bits (2 bytes = 1 word)
	"""
	def register_value(self, a_register_index, a_register_length):
		assert self.is_connected(), "register_value->device is not connected"
		try:

			#Starting add, num of reg to read, slave unit.
			l_result = self.__modbus_client.read_holding_registers(a_register_index, a_register_length, unit=self.SLAVE_UNIT_NUMBER) # Average current
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
			self.__logger.exception("register:Exception occured" + l_e.message)
		finally:
#			self.__logger.info("register:".join(str(e) for e in result))
			return l_result

	"""
	Returns the csv file path
	"""
	def get_csv_file_path(self):
		#require
		assert self.__args.host_ip, "host ip is empty"
		assert self.__args.host_mac, "host mac is empty"
		if __debug__:
			try:
				socket.inet_aton(self.__args.host_ip)
			except socket.error as l_e:
				assert False, "Host ip address is invalid"
				raise l_e

		l_dir = self.DEFAULT_CSV_FILE_LOCATION + '/' + str(datetime.today().year) + '/' + '{:02d}'.format(datetime.today().month)
		l_result = l_dir + '/' \
			+ datetime.today().strftime('%Y%m%d') + '_' + self.__args.host_mac.replace(':', '-') + '_' + self.__args.host_ip + '_' + os.path.basename(__file__) + '.csv'

		try:
			os.makedirs(l_dir)
		except OSError as l_e:
			if l_e.errno == errno.EEXIST:
				pass
			else:
				self.__logger.error('get_csv_file_path Error: %s' % (l_e))
				raise

		return l_result


	"""
	Posts given values disctionnary to solarity platform
	"""
	def post_to_sit_platform(self, a_values_dictionnary):
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


	"""
	Sets json data
	"""
	def set_json_data(self, a_values_dictionnary):
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

	"""
	Returns web service URL with object_type
	"""
	def service_url(self, a_values_dictionnary):
		assert a_values_dictionnary.has_key('sit_platform_object_type')
		assert self.__base_url.endswith("/")

		result = self.__base_url + a_values_dictionnary['sit_platform_object_type'] 

		return result

	"""
	@returns an array with a row to store into csv corresponding to self.CSV_HEADER_ROW
	"""
	def get_csv_row(self):
		l_modbus_slave_address = 1 #Default 1
		l_ip_address = self.__args.host_ip
		self.__logger.info("-->IP:%s MAC:%s" % (l_ip_address, self.__args.host_mac))	
		l_timeout = 2.0 #Default 2.0
		l_result = OrderedDict()

		try:
			l_result['Timestamp'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
			
			#l_result['someVal'] = self.register_value(0xC851, 2) #Phase to phase voltage
			#l_result['someVal'] = self.register_value(0xC858, 1) #Current l1
			#l_result['V1'] = self.register_value(0xC558, 2) #Current l1
			l_result['Hours'] = '{:.2f}'.format(self.register_values_u_long(0xC550)/100) #Hour meter
			l_result['U12'] = '{:.2f}'.format(self.register_values_u_long(0xC552)/100) #Phase to phase voltage 1-2
			l_result['U23'] = '{:.2f}'.format(self.register_values_u_long(0xC554)/100) #Phase to phase voltage 2-3
			l_result['U31'] = '{:.2f}'.format(self.register_values_u_long(0xC556)/100) #Phase to phase voltage 3-1
			l_result['V1'] = '{:.2f}'.format(self.register_values_u_long(0xC558)/100) #Simple voltage l1
			l_result['V2'] = '{:.2f}'.format(self.register_values_u_long(0xC55A)/100) #Simple voltage l2
			l_result['V3'] = '{:.2f}'.format(self.register_values_u_long(0xC55C)/100) #Simple voltage l3
			l_result['F'] = '{:.2f}'.format(self.register_values_u_long(0xC55E)/100) #Frequency
			l_result['I1'] = '{:.3f}'.format(self.register_values_u_long(0xC560)/1000) #Current l1
			l_result['I2'] = '{:.3f}'.format(self.register_values_u_long(0xC562)/1000) #Current l2
			l_result['I3'] = '{:.3f}'.format(self.register_values_u_long(0xC564)/1000) #Current l3
			l_result['In'] = '{:.2f}'.format(self.register_values_u_long(0xC566)/100) #Neutral current
			l_result['P'] = '{:.2f}'.format(self.register_values_s_long(0xC568)/100) #Active power kW
			l_result['Q'] = '{:.2f}'.format(self.register_values_s_long(0xC56A)/100) #Reactive power
			l_result['S'] = '{:.2f}'.format(self.register_values_s_long(0xC56C)/100) #Apparent power
			l_result['PF'] = '{:.3f}'.format(self.register_values_s_long(0xC56E)/1000) #Power factor
			l_result['P1'] = '{:.2f}'.format(self.register_values_s_long(0xC570)/100) #Active power l1 kW
			l_result['P2'] = '{:.2f}'.format(self.register_values_s_long(0xC572)/100) #Active power l2 kW
			l_result['P3'] = '{:.2f}'.format(self.register_values_s_long(0xC574)/100) #Active power l3 kW
			l_result['Q1'] = '{:.2f}'.format(self.register_values_s_long(0xC576)/100) #Reactive power l1
			l_result['Q2'] = '{:.2f}'.format(self.register_values_s_long(0xC578)/100) #Reactive power l2
			l_result['Q3'] = '{:.2f}'.format(self.register_values_s_long(0xC57A)/100) #Reactive power l3
			l_result['S1'] = '{:.2f}'.format(self.register_values_u_long(0xC57C)/100) #Apparent power l1
			l_result['S2'] = '{:.2f}'.format(self.register_values_u_long(0xC57E)/100) #Apparent power l2
			l_result['S3'] = '{:.2f}'.format(self.register_values_u_long(0xC580)/100) #Apparent power l3
			l_result['PF1'] = '{:.3f}'.format(self.register_values_s_long(0xC582)/1000) #Power factor l1 Power Factor phase 1 -: leading and + : lagging : 
			l_result['PF2'] = '{:.3f}'.format(self.register_values_s_long(0xC584)/1000) #Power factor l2
			l_result['PF3'] = '{:.3f}'.format(self.register_values_s_long(0xC586)/1000) #Power factor l3

			l_result['HoursMaxAvg'] = '{:.2f}'.format(self.register_values_u_long(0xC650)/100) #Hour meter
			l_result['Ea+'] = self.register_values_u_long(0xC65C) #Partial Positive Active Energy: Ea+
			l_result['Er+'] = self.register_values_u_long(0xC65E) #Partial Positive Reactive Energy: Er +
			#Max/Average
			l_result['MaxAvgI1'] = '{:.3f}'.format(self.register_values_u_long(0xC77E)/1000) #Max/avg current 1
			l_result['MaxAvgI2'] = '{:.3f}'.format(self.register_values_u_long(0xC780)/1000) #Max/avg current 2
			l_result['MaxAvgI3'] = '{:.3f}'.format(self.register_values_u_long(0xC782)/1000) #Max/avg current 3
			l_result['MaxAvgIn'] = '{:.3f}'.format(self.register_values_u_long(0xC784)/1000) #Max/avg current neutral
			l_result['MaxAvgP+'] = '{:.2f}'.format(self.register_values_u_long(0xC786)/100) #Max/avg P+
			l_result['MaxAvgP-'] = '{:.2f}'.format(self.register_values_u_long(0xC788)/100) #Max/avg P-
			l_result['MaxAvgQ+'] = '{:.2f}'.format(self.register_values_u_long(0xC78A)/100) #Max/avg Q+
			l_result['MaxAvgQ-'] = '{:.2f}'.format(self.register_values_u_long(0xC78C)/100) #Max/avg Q-
			l_result['MaxAvgS'] = '{:.2f}'.format(self.register_values_u_long(0xC78E)/100) #Max/avg E
			# Harmonic THD values in %
			l_result['ThdU12'] = '{:.1f}'.format(self.register_values_u_word(0xC950)/10) #thd U12
			l_result['ThdU23'] = '{:.1f}'.format(self.register_values_u_word(0xC951)/10) #thd U23
			l_result['ThdU31'] = '{:.1f}'.format(self.register_values_u_word(0xC952)/10) #thd U31
			l_result['ThdV1'] = '{:.1f}'.format(self.register_values_u_word(0xC953)/10) #thd V1
			l_result['ThdV2'] = '{:.1f}'.format(self.register_values_u_word(0xC954)/10) #thd V2
			l_result['ThdV3'] = '{:.1f}'.format(self.register_values_u_word(0xC955)/10) #thd V3
			l_result['ThdI1'] = '{:.1f}'.format(self.register_values_u_word(0xC956)/10) #thd I1
			l_result['ThdI2'] = '{:.1f}'.format(self.register_values_u_word(0xC957)/10) #thd I2
			l_result['ThdI3'] = '{:.1f}'.format(self.register_values_u_word(0xC958)/10) #thd I3
			l_result['ThdIn'] = '{:.1f}'.format(self.register_values_u_word(0xC959)/10) #thd In

			#l_result['someVal'] = self.register_value(51288, 1) #Current l1
			#self.__logger.debug("someVal shit: %s" % l_result['someVal'].getRegister(0))
			#print("******* TESTS ***********************")
			#print (self.register_value(0xC857, 2)) #Frequency
			#print(l_result['someVal'].decode(word_order=little, byte_order=little, formatters=float64))

			self.__logger.info("get_csv_row: %s" % ', '.join(['{}:{}'.format(k,v) for k,v in l_result.items()]))
			#print(l_device.inverter)

			return l_result
		except Exception as l_e:
			self.__logger.exception("get_csv_row->Exception occured: %s" % (l_e))
			self.__logger.error('get_csv_row->Error: %s' % (l_e))
			raise l_e
		

	"""
	from spec returns a word from given register index
	@a_register_index: a register index
	"""
	def register_values_u_word(self, a_register_index):
		l_register_res = self.register_value(a_register_index, 1)
		#self.__logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		l_result = decoder.decode_16bit_uint()
		self.__logger.debug("register_values_u_word->after decoder:%s" % l_result)
		return l_result

	"""
	from spec returns a long from given register index
	@a_register_index: a register index
	"""
	def register_values_s_long(self, a_register_index):
		l_register_res = self.register_value(a_register_index, 2)
		#self.__logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		l_result = decoder.decode_32bit_int()
		self.__logger.debug("register_values_s_long->after decoder:%s" % l_result)
		return l_result

	"""
	from spec returns a long from given register index
	@a_register_index: a register index
	"""
	def register_values_u_long(self, a_register_index):
		l_register_res = self.register_value(a_register_index, 2)
		#self.__logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		l_result = decoder.decode_32bit_uint()
		self.__logger.debug("register_values_u_long->after decoder:%s" % l_result)
		return l_result
	
	"""
	Stores values into CSV DEFAULT_CSV_FILE_LOCATION
	@param a_row_dict: a dictionnary as row 
	"""
	def store_values_into_csv(self, a_row_dict):
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
			self.__logger.exception("disconnect->Exception occured" + l_e.message)
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
	l_o = Legrand145671()
	try:
		l_o.connect()
		l_o.process_script_arguments()
	except Exception as l_e:
		logger.exception("disconnect:Exception occured" + l_e.message)
		raise l_e
	finally:
		if l_o.is_connected():
			l_o.disconnect()



if __name__ == '__main__':
    main()
