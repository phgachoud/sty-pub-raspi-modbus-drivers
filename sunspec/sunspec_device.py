#!/usr/bin/env python
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#       DESCRIPTION: 
#           Wrapper over sunspec to log content into a csv file, more infos with --help
#
#			Logging into /var/log/solarity/file_name.log
#
#       IMPROVEMENTS:
#			Hope to be able one day to merge it with other more abstract modules such as cluster_controller.py
#
#       CALL SAMPLE:
#               Usage /data/solarity/sit-raspi/sty-pub-raspi-modbus-drivers/sunspec/sunspec_device.py --host_ip '192.168.0.68' --host_mac 'b8:27:eb:e6:bb:3f' --longitude='-70.941830' --lattitude='-33.669959' --store_values --device_type='abb' -v -t --slave_address=126
#			A typical call into a cronjob
#				* 5-23 * * * /data/solarity/sit-raspi/sty-pub-raspi-modbus-drivers/sunspec/sunspec_device.py --host_ip '192.168.0.68' --host_mac 'b8:27:eb:e6:bb:3f' --longitude='-70.941830' --lattitude='-33.669959' --store_values --device_type='abb' -v -t --slave_address=126
#		
#		REQUIRE
#			sudo apt-get install python3-serial or sudo apt-get install python-serial
#			sunspec dependency: git submodule update --init --recursive
#			sudo apt install python3-pip
#			sudo pip3 install serial #in case of error unsupported operand type(s) for -=: 'Retry' and 'int' sudo pip3 install --upgrade setuptools
#
#       CALL PARAMETERS:
#               1) 
#
#		*************************************************************************************************
#       @author: Philippe Gachoud
#       @creation: 20190327
#       @last modification:
#       @version: 1.0
#		*************************************************************************************************
#		Copyright (C) 2020 Solarity spa

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
#
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# INCLUDES
try:
	import sys
	import os.path
	import os, errno
	import logging # http://www.onlamp.com/pub/a/python/2005/06/02/logging.html
	from logging import handlers
	sys.path.append(os.path.join(os.path.dirname(__file__), '../lib')) #the way to import directories
	sys.path.append(os.path.join(os.path.dirname(__file__), '../lib/third_party')) #the way to import directories
	import argparse
	import csv
	import socket
	sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pysunspec'))
	import sunspec.core.client as client
	import sunspec.core.suns as suns
	from pprint import pprint
	from datetime import datetime, date, time, timedelta
	sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'SunriseSunsetCalculator'))
	from sunrise_sunset import SunriseSunset
	from pprint import pprint
	from sit_constants import SitConstants
#	import jsonpickle # pip install jsonpickle
#	import json
except ImportError as l_err:
	print("ImportError: {0}".format(l_err))
	raise l_err

class SunspecDevice(object):

# CONSTANTS
	LOG_FILE_PATH = '/var/log/solarity'
	DEFAULT_LOGGING_LEVEL = logging.INFO #For console overrided by --verbose
	DEFAULT_FILE_LOGGING_LEVEL = logging.DEBUG #For file
	DEFAULT_CSV_FILE_LOCATION = '/var/solarity' #without ending slash
	CSV_HEADER_ROW = ['Timestamp', 'A', 'AphA', 'AphB', 'AphC', 'PPVphAB', 'PPVphBC', 'PPVphCA', 'PhVphA', 'PhVphB', 'PhVphC', 'W', 'Hz', 'VA', 'VAr', 'PF', 'WH', 'DCA', 'DCW', 'TmpCab', 'TmpSnk', 'TmpOt', 'St', 'StVnd', 'Evt1', 'Evt2', 'EvtVnd1', 'EvtVnd2', 'EvtVnd3', 'EvtVnd4']
	DEVICE_TYPES_ARRAY = ['abb', 'sma']
	SECONDS_INTERVAL_FOR_SUNRISE_VALIDATION = 120
	SECONDS_INTERVAL_FOR_SUNSET_VALIDATION = 0
	DEFAULT_SLAVE_ADDRESS = 1
	PARSER_DESCRIPTION = 'Actions with sunspec device. ' + SitConstants.DEFAULT_HELP_LICENSE_NOTICE


# VARIABLES
	__logger = None

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
			self.init_arg_parse()
			#*** Logger
			fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
			self.__logger = logging.getLogger(__name__) 
			self.__logger.propagate = False
			self.__logger.setLevel(logging.DEBUG)
			self.__console_handler = logging.StreamHandler(sys.stdout)
			self.__console_handler.setFormatter(fmt)
			self.__console_handler.setLevel(self.DEFAULT_LOGGING_LEVEL)

			self.__file_handler = handlers.RotatingFileHandler("{0}/{1}_{2}.log".format(self.LOG_FILE_PATH, os.path.basename(__file__), self.__args.host_mac.replace(':', '-')), maxBytes=5242880, backupCount=10)
			self.__file_handler.setFormatter(fmt)
			self.__file_handler.setLevel(self.DEFAULT_FILE_LOGGING_LEVEL)

			self.__logger.addHandler(self.__file_handler)
			self.__logger.addHandler(self.__console_handler)
		except OSError as l_e:
			self.__logger.warning("init-> OSError, probably rollingfileAppender" % (l_e))
			if e.errno != errno.ENOENT:
				raise
		except Exception as l_e:
			print('Error in init: %s' % (l_e))
			#exit(1)
		


	def init_arg_parse(self):
		"""
			Parsing arguments
		"""
		self.__parser = argparse.ArgumentParser(description=self.PARSER_DESCRIPTION)
		self.__parser.add_argument('-v', '--verbose', help='increase output verbosity', action="store_true")
		self.__parser.add_argument('-s', '--store_values', help='Stores values into csv file located into ' + self.DEFAULT_CSV_FILE_LOCATION, action="store_true")
		self.__parser.add_argument('-t', '--test', help='Runs test method', action="store_true")
		self.__parser.add_argument('-y', '--display_all', help='Displays all attributes found for sunspec device', action="store_true")
		
		#self.__parser.add_argument('-u', '--base_url', help='NOT_IMPLEMENTED:Gives the base URL for requests actions', nargs='?', default=self.DEFAULT_BASE_URL)
		l_required_named = self.__parser.add_argument_group('required named arguments')
		l_required_named.add_argument('-i', '--host_ip', help='Host IP', nargs='?', required=True)
		l_required_named.add_argument('-u', '--slave_address', help='Slave address of modbus device', nargs='?', required=True)
		l_required_named.add_argument('-m', '--host_mac', help='Host MAC', nargs='?', required=True)
		l_required_named.add_argument('-l', '--longitude', help='Longitude coordinate (beware timezone is set to Chile)', nargs='?', required=True)
		l_required_named.add_argument('-a', '--lattitude', help='Lattitude coordinate (beware timezone is set to Chile)', nargs='?', required=True)
		l_required_named.add_argument('-d', '--device_type', help='Device Type:' + ('|'.join(str(l) for l in self.DEVICE_TYPES_ARRAY)), nargs='?', required=True)
		args = self.__parser.parse_args()
		self.__args = args

	def execute_corresponding_args( self ):
		"""
			Parsing arguments and calling corresponding functions
		"""
		if self.__args.test:
			self.test()
		if self.__args.verbose:
			self.__logger.setLevel(logging.DEBUG)
			self.__console_handler.setLevel(logging.DEBUG)
			self.__file_handler.setLevel(logging.DEBUG)
		else:
			self.__logger.setLevel(logging.DEBUG)
			self.__console_handler.setLevel(logging.ERROR)
			self.__file_handler.setLevel(logging.DEBUG)
			
		if self.__args.store_values:
			if self.device_is_reachable():
				l_device = self.get_device()
				self.store_values_into_csv(self.get_csv_row(l_device), l_device)


	def device_is_reachable(self):
		"""
		Is Device reachable if abb device
			going through sunset-sunrise and self.DEVICE_TYPES_ARRAY
		"""
		if self.__args.device_type == 'sma':
			l_result = True
			self.__logger.info("Device type is SMA, no sunset sunrise check, always true")
		else:
			l_ss = SunriseSunset(datetime.now(), latitude=float(self.__args.lattitude),
			longitude=float(self.__args.longitude), localOffset=-3)
			self.__logger.info("device_is_reachable-> longitude:%s lattitude:%s" % (self.__args.longitude, self.__args.lattitude))
			l_rise_time, l_set_time = l_ss.calculate()
			l_result = l_rise_time + timedelta(seconds=self.SECONDS_INTERVAL_FOR_SUNRISE_VALIDATION) < datetime.now() and \
				l_set_time - timedelta(seconds=self.SECONDS_INTERVAL_FOR_SUNSET_VALIDATION) > datetime.now()
			self.__logger.info("device_is_reachable-> rise_time:%s set_time:%s now:%s result (sun is up?):%s" % (l_rise_time, l_set_time, datetime.now(), l_result))

		return l_result

	def display_all(self):
		"""
		"""

	def test(self):
		"""
			Test function
		"""

		try:
			l_d = self.get_device()

			self.__display_all_properties(l_d)
			#self.__logger.info("-->device")	
			#print d.device
#			self.__logger.info("-->models")	
#			print l_d.models
#			self.__logger.info("-->common")	
#			print l_d.common
#			self.__logger.info("-->inverter ************* repeating *************")	
#			print (l_d.inverter.repeating)
			print ("################# BEGIN #################")
			self.__logger.info("--> ************* device models *************: %s" % (l_d.models))	 #Lists properties to be loaded with l_d.<property>.read() and then access them
			self.__logger.info("-->inverter ************* l_d.inverter.points *************: %s" % (l_d.inverter.points))	#Gives the inverter available properties
			self.__logger.info("-->inverter ************* common *************: %s" % (l_d.common))	
			self.__logger.info("-->inverter ************* common Serial Number *************: %s" % (l_d.common.SN))	
#			pprint(vars(l_d.common.model.device))
			#pprint(vars(l_d.common.model.device))
			#l_serialized = jsonpickle.encode(d)
			#print(json.dumps(json.loads(l_serialized), indent=2))
			#pprint(vars(d))
			print ("################# END #################")
#			print (l_d.inverter.model)
#			self.__logger.info("--> repeating_name")	
#			print l_d.volt_var.repeating_name
			#print("Test function")
			#print(l_d.inverter)
#			self.__logger.info("--> voltages DC 3 phases")#Not implemented for model 103
#			print l_d.volt_var#Not implemented for model 103



		except client.SunSpecClientError as l_e:
			print('Error: %s' % (l_e))
			self.__logger.error('Error: %s' % (l_e))
			sys.exit(1)
		except Exception as l_e:
			self.__logger.exception("Exception occured: %s" % (l_e))
			print('Error: %s' % (l_e))
			self.__logger.error('Error: %s' % (l_e))
			sys.exit(1)

	def __display_all_properties (self, a_device):
		"""
		@param a_device
		@return: nothing
		"""
		print ("################# Device Properties Begin #################")

		for model in a_device.device.models_list:
			if model.model_type and model.model_type.label:
				label = '%s (%s)' % (model.model_type.label, str(model.id))
			else:
				label = '(%s)' % (str(model.id))
			print('\nmodel: %s\n' % (label))
			for block in model.blocks:
				if block.index > 0:
					index = '%02d:' % (block.index)
				else:
					index = '   '
				for point in block.points_list:
					if point.value is not None:
						if point.point_type.label:
							label = '   %s%s (%s):' % (index, point.point_type.label, point.point_type.id)
						else:
							label = '   %s(%s):' % (index, point.point_type.id)
						units = point.point_type.units
						if units is None:
							units = ''
						if point.point_type.type == suns.SUNS_TYPE_BITFIELD16:
							value = '0x%04x' % (point.value)
						elif point.point_type.type == suns.SUNS_TYPE_BITFIELD32:
							value = '0x%08x' % (point.value)
						else:
							value = str(point.value).rstrip('\0')
						print('%-40s %20s %-10s' % (label, value, str(units)))

		print ("################# Device Properties End #################")


	def get_property_value(self, a_sun_spec_client_device_property):
		"""
		@param a_sun_spec_client_device_property: 
		@return: nothing
		"""

		try:
			return a_sun_spec_client_device_property
		except Exception as l_e:
			self.__logger.error('Error: %s' % (l_e))
			raise l_e

	"""
	Returns the full path of csv file
		creates directory if not exists and raises exception if can't
	"""
	def get_csv_file_path(self):
		#require
		self.__logger.debug("host ip:%s" % self.__args.host_ip)
		assert self.__args.host_ip, "host ip is empty"
		assert self.__args.host_mac, "host mac is empty"
		if __debug__:
			try:
				socket.inet_aton(self.__args.host_ip)
			except socket.error:
				assert False, "Host ip address is invalid"

		l_dir = self.DEFAULT_CSV_FILE_LOCATION + '/' + str(datetime.today().year) + '/' + str(datetime.today().month)
		l_result = l_dir + '/' \
			+ datetime.today().strftime('%Y%m%d') + '_' + self.__args.host_mac.replace(':', '-') + '_' + self.__args.host_ip 
		if self.__args.slave_address:
			l_result = l_result + '_' + self.__args.slave_address
		else:
			l_result = l_result + '_' + self.DEFAULT_SLAVE_ADDRESS
			
		l_result = l_result + '_' + os.path.basename(__file__) + '.csv'

		try:
			os.makedirs(l_dir)
		except OSError as l_e:
			if l_e.errno == errno.EEXIST:
				pass
			else:
				self.__logger.error('get_csv_file_path Error: %s' % (l_e))
				raise

		return l_result

	def get_device(self):
		"""
		@returns a device with inverter properties read
		"""
		l_modbus_slave_address = self.DEFAULT_SLAVE_ADDRESS #Default 1
		if self.__args.slave_address:
			l_modbus_slave_address = self.__args.slave_address
		l_ip_address = self.__args.host_ip
		self.__logger.info("-->IP:%s MAC:%s Slave_address:%s " % (l_ip_address, self.__args.host_mac, l_modbus_slave_address))
		l_timeout = 2.0 #Default 2.0

		try:
			l_device = client.SunSpecClientDevice(client.TCP, l_modbus_slave_address, ipaddr=l_ip_address, timeout=l_timeout)
			l_device.common.read() # retreives latest inverter model contents
			l_device.inverter.read() # retreives latest inverter model contents

			return l_device
		except client.ModbusClientError as l_e:
			self.__logger.error('ModbusClientError: %s' % (l_e))
			raise l_e
		except client.SunSpecClientError as l_e:
			self.__logger.error('SunspecClientError: %s' % (l_e))
			raise l_e
		except Exception as l_e:
			self.__logger.exception("Exception occured: %s" % (l_e))
			self.__logger.error('Error: %s' % (l_e))
			raise l_e

	def get_csv_row(self, a_device):
		"""
		@returns an array with a row to store into csv corresponding to self.CSV_HEADER_ROW
		"""

		l_result = []
		try:
			l_result.append(datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'))
			l_result.append(a_device.inverter.A)
			l_result.append(a_device.inverter.AphA)
			l_result.append(a_device.inverter.AphB)
			l_result.append(a_device.inverter.AphC)
			l_result.append(a_device.inverter.PPVphAB)
			l_result.append(a_device.inverter.PPVphBC)
			l_result.append(a_device.inverter.PPVphCA)
			l_result.append(a_device.inverter.PhVphA)
			l_result.append(a_device.inverter.PhVphB)
			l_result.append(a_device.inverter.PhVphC)
			l_result.append(a_device.inverter.W)
			l_result.append(a_device.inverter.Hz)
			l_result.append(a_device.inverter.VA)
			l_result.append(a_device.inverter.VAr)
			l_result.append(a_device.inverter.PF)
			l_result.append(a_device.inverter.WH)
			l_result.append(a_device.inverter.DCA)
			#DONT HAVE IT l_result.append(a_device.inverter.DCV)
			l_result.append(a_device.inverter.DCW)
			l_result.append(a_device.inverter.TmpCab)
#			self.__logger.debug("get_csv_row: PhVphA:%s" % type(l_device.inverter.PhVphA).__name__)
#			self.__logger.debug("get_csv_row: PhVphA:%s" % repr(l_device.inverter.PhVphA))
			l_result.append(a_device.inverter.TmpSnk)
			# DONT HAVE IT l_result.append(l_device.inverter.TmpTrns)
			l_result.append(a_device.inverter.TmpOt)
			l_result.append(a_device.inverter.St)
			l_result.append(a_device.inverter.StVnd)
			l_result.append(a_device.inverter.Evt1)
			l_result.append(a_device.inverter.Evt2)
			l_result.append(a_device.inverter.EvtVnd1)
			l_result.append(a_device.inverter.EvtVnd2)
			l_result.append(a_device.inverter.EvtVnd3)
			l_result.append(a_device.inverter.EvtVnd4)
			#self.__logger.debug("get_csv_row: l_result:%s" % ('|'.join(str(l) for l in map(str, l_result))))
			self.__logger.info("get_csv_row: %s" % ('|'.join(str(l) for l in map(str, l_result))))
			#print(l_device.inverter)

			return l_result
		except client.ModbusClientError as l_e:
			self.__logger.error('ModbusClientError: %s' % (l_e))
			sys.exit(0)
		except client.SunSpecClientError as l_e:
			self.__logger.error('SunspecClientError: %s' % (l_e))
			sys.exit(1)
		except Exception as l_e:
			self.__logger.exception("Exception occured: %s" % (l_e))
			self.__logger.error('Error: %s' % (l_e))
			sys.exit(1)

	def write_csv_header(self, a_device, a_csv_writter):
		"""
		writes header data with # at the begining of the line for meta data of the device
				http://www.w3.org/TR/tabular-data-model/#embedded-metadata
				https://stackoverflow.com/questions/18362864/adding-metadata-identifier-data-to-a-csv-file
		@param a_device: a device
		@param a_csv_writter: self explaining
		raises exceptions
		"""
		try:
			a_device.common.read()
			#Ip address of device
			l_row = []
			l_row.append('#Ip')
			l_row.append(self.__args.host_ip)
			a_csv_writter.writerow(l_row)
			#MAC address of device
			l_row = []
			l_row.append('#MAC')
			l_row.append(self.__args.host_mac)
			a_csv_writter.writerow(l_row)
			#Slave address of device
			l_row = []
			l_row.append('#Slave_address')
			l_row.append(self.__args.slave_address)
			a_csv_writter.writerow(l_row)
			#Model name
			l_row = []
			l_row.append('#Mn')
			l_row.append(a_device.common.Mn)
			a_csv_writter.writerow(l_row)
			#Model device
			l_row = []
			l_row.append('#Md')
			l_row.append(a_device.common.Md)
			a_csv_writter.writerow(l_row)
			#Model Version
			l_row = []
			l_row.append('#Vr')
			l_row.append(a_device.common.Vr)
			a_csv_writter.writerow(l_row)
			#Model Serial Number
			l_row = []
			l_row.append('#SN')
			l_row.append(a_device.common.SN)
			a_csv_writter.writerow(l_row)
			#Header row
			a_csv_writter.writerow(self.CSV_HEADER_ROW)
		except client.ModbusClientError as l_e:
			self.__logger.error('ModbusClientError: %s' % (l_e))
			raise l_e
		except client.SunSpecClientError as l_e:
			self.__logger.error('SunspecClientError: %s' % (l_e))
			raise l_e
		except Exception as l_e:
			self.__logger.exception("Exception occured: %s" % (l_e))
			self.__logger.error('Error: %s' % (l_e))
			raise l_e

		
	
	def store_values_into_csv(self, a_row, a_device):
		"""
		Stores values into CSV DEFAULT_CSV_FILE_LOCATION
		@param l_row: an array of values
		@param a_device: a device
		"""

		try:
			l_f_name = self.get_csv_file_path()
			l_file_exists = os.path.isfile(l_f_name)
			self.__logger.info("Writting into file %s exists:%s" % (l_f_name, l_file_exists))
			with open(l_f_name, mode='a+') as l_csv_file:
				l_csv_writter = csv.writer(l_csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
				if not l_file_exists:
					self.__logger.info("Writting HEADER row: %s" % (';'.join(str(l) for l in self.CSV_HEADER_ROW)))
					self.write_csv_header(a_device, l_csv_writter)
				self.__logger.info("HEADER row: %s" % (';'.join(str(l) for l in self.CSV_HEADER_ROW)))
				self.__logger.info("Writting row: %s" % (';'.join(str(l) for l in a_row)))
				l_csv_writter.writerow(a_row)
		except Exception as l_e:
			self.__logger.error('Error: %s' % (l_e))
			raise l_e



"""
Main method
"""
def main():
	#logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, filemode="a+", format="%(asctime)-15s %(levelname)-8s %(message)s")
	logger = logging.getLogger(__name__)

	try:
		l_obj = SunspecDevice()
		l_obj.execute_corresponding_args()
#		l_id.test()
		pass
	except KeyboardInterrupt:
		logger.exception("Keyboard interruption")
	except Exception:
		logger.exception("Exception occured")
	finally:
		logger.info("Main method end -- end of script")



if __name__ == '__main__':
    main()
