#!/usr/bin/env python3
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#       DESCRIPTION: 
#            Modbus interface for any device conected to SMA cluster_controller
#
#            -h or --help for more informations about use
#
#
#
#
#
#
#       CALL SAMPLE:
#			/data/solarity/sit-raspi/modbus/cluster_controller_inverter.py --host_ip '192.168.0.74' --host_mac '00:90:E8:73:0A:D6' --store_values --raise_event --slave_address 3-7
#	
#	REQUIRE
#		**** PYTHON *****
#		sudo apt-get install python-pygments python-pip python-pymodbus python3-pip
#		sudo pip install -U pymodbus click requests  
#
#		**** PYTHON 3 *****
#		sudo apt install python3-pip
#		sudo pip3 install requests click pymodbus 
#
#       CALL PARAMETERS:
#               1) 
#
#       @author: Philippe Gachoud
#       @creation: 20200423
#       @last modification:
#       @version: 1.0
#       @URL: $URL
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# INCLUDES
try:
	import sys
	import os, errno
	sys.path.append(os.path.join(os.path.dirname(__file__), 'lib')) #the way to import directories
	sys.path.append(os.path.join(os.path.dirname(__file__), 'lib/register_types')) #the way to import directories
	sys.path.append(os.path.join(os.path.dirname(__file__), '../lib/third_party/SunriseSunsetCalculator')) #the way to import directories
	from pymodbus.constants import Endian
	from pymodbus.exceptions import ModbusException
	import logging # http://www.onlamp.com/pub/a/python/2005/06/02/logging.html
	from logging import handlers
	import argparse
	#sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pysunspec'))
	from datetime import datetime, date, time, timedelta
	import subprocess
	from collections import OrderedDict
	from sit_logger import SitLogger
	from sit_modbus_device import SitModbusDevice #from file_name import ClassName
	from sit_modbus_register import SitModbusRegister
	from sit_modbus_register_event import SitModbusRegisterEvent
	from cluster_controller import ClusterController
	from register_type_int16_u import RegisterTypeInt16u
	from register_type_int16_s import RegisterTypeInt16s
	from register_type_int32_u import RegisterTypeInt32u
	from register_type_int32_s import RegisterTypeInt32s
	from register_type_int64_u import RegisterTypeInt64u
	from register_type_sma_cc_device_class import RegisterTypeSmaCCDeviceClass
	from sit_date_time import SitDateTime
	from sit_json_conf import SitJsonConf
	from sit_utils import SitUtils
except ImportError as l_err:
	print("ImportError: {0}".format(l_err))
	print(sys.path)
	raise l_err

class ClusterControllerInverter(ClusterController):

# CONSTANTS

	DEFAULT_SLAVE_ADDRESS = 3
	MIN_W_FOR_RAISE_EVENT_GENERATION = 2000
	PARSER_DESCRIPTION = 'Actions with sma cluster controller inverter.  ' + SitConstants.DEFAULT_HELP_LICENSE_NOTICE

# CLASS ATTRIBUTES

	_byte_order = Endian.Big
	_word_order = Endian.Big
	_substract_one_to_register_index = False

	_slave_addresses_list = None
	_current_read_device_class = None
	_last_read_slave_address = None
	_last_read_serial_number = None

# INITIALIZE

	"""
		Initialize
	"""
	def __init__(self, a_slave_address=DEFAULT_SLAVE_ADDRESS, a_port=ClusterController.DEFAULT_MODBUS_PORT, an_ip_address=None):
		"""
		slave_address priority to commandline arguments
		"""
		assert self.valid_slave_address(a_slave_address), 'init invalid slave address'
		try:
			self.init_arg_parse()
			l_slave_address = a_slave_address
			if (hasattr(self._args, 'slave_address') and self._args.slave_address):
				self._slave_addresses_list = SitUtils.args_to_list(self._args.slave_address)

			assert self.valid_slave_address_list(self._slave_addresses_list), 'Given script arguments are not valid, or could not be parsed'
			assert self.valid_ip(self._args.host_ip), 'valid ip address:{}'.format(self._args.host_ip)

			super().__init__(l_slave_address, a_port=a_port, an_ip_address=self._args.host_ip) 
			self._logger = SitLogger().new_logger(self.__class__.__name__, self._args.host_mac)

			self.invariants()
			#self._logger.debug('init->' + self.out())
		except OSError as l_e:
			self._logger.warning("init-> OSError, probably rollingfileAppender" % (l_e))
			if e.errno != errno.ENOENT:
				raise l_e
		except Exception as l_e:
			print('Error in init: %s' % (l_e))
			raise l_e
			#exit(1)

	def _init_sit_modbus_registers(self, a_slave_address):
		"""
			Initializes self._sit_modbus_registers
		"""
		self.add_cc_only_sit_modbus_registers(a_slave_address)
		#self.add_common_sit_modbus_registers(a_slave_address)

		self.invariants()


	def add_common_sit_modbus_registers(self, a_slave_address):
		"""
		COMMON REGISTERS to ClusterController and Inverters
		"""
		super().add_common_sit_modbus_registers(a_slave_address)
#		l_reg_list = OrderedDict()
#
#		#PARAMETERS UNIT_ID = 2 (p.26 of doc)
#		SitUtils.od_extend(l_reg_list, RegisterTypeInt64u('Wh2', 'Total energy fed in across all line conductors, in Wh (accumulated values of the inverters) System param', 30513, SitModbusRegister.ACCESS_MODE_R, 'Wh', an_is_metadata=False, a_slave_address=2))
#
#		self.append_modbus_registers(l_reg_list)


# MODBUS READING

	def read_all_sit_modbus_registers(self):
		"""
			Reads all registers and print result as debug
		"""
		self._logger.debug('read_all_sit_modbus_registers-> registers to read count({}) start --------------------------------------------------'.format(len(self._sit_modbus_registers)))

		for l_short_desc, l_sit_reg in self._sit_modbus_registers.items():
			self.read_sit_modbus_register(l_sit_reg)
			# Setting slave address if changed
			if self._last_read_slave_address != l_sit_reg.slave_address:
				self._current_read_device_class = None
				self._last_read_serial_number = None
				self._last_read_slave_address = l_sit_reg.slave_address
			#Setting device class
			if l_sit_reg.short_description == 'DeviceClass':
				self._current_read_device_class = l_sit_reg.value
			elif l_sit_reg.short_description == 'SN':
				self._last_read_serial_number = l_sit_reg.value
			if l_sit_reg.has_post_set_value_call():
				l_sit_reg.call_post_set_value()
			#self._logger.debug('read_all_registers-> sit_register.out():%s' % (l_sit_reg.out()))
			self._logger.debug('read_all_registers-> sit_register.out_short():%s' % (l_sit_reg.out_short()))


# EVENTS


	def _W_event(self, a_sit_modbus_register):
		"""
		REDEFINE

		Called by modbus_device.call_sit_modbus_registers_events()
		"""

		if 'PV inverter' in self._current_read_device_class:
			super()._W_event(a_sit_modbus_register)

	def _setted_parts(self, a_subject, a_body):
		"""
		return subject and body
		"""
		l_sub = a_subject + ' SN:{}'.format(self._last_read_serial_number)
		l_body = a_body
		return l_sub, l_body

# IMPLEMENTATION


# EXECUTE ARGS

	"""
		Parsing arguments and calling corresponding functions
	"""
	def execute_corresponding_args(self):
		try:
			self.connect()
			if self._args.verbose:
				self._logger.setLevel(logging.DEBUG)
			else:
				self._logger.setLevel(logging.INFO)
			if self._args.store_values or self._args.display_all or self._args.test or self._args.raise_event:
				assert self.valid_slave_address_list(self._slave_addresses_list), 'Slave addresses list is invalid:{}'.format(self._slave_addresses_list)
				self._logger.debug('execute_corresponding_args-> _slave_addresses_list:{}'.format(self._slave_addresses_list))
				# FOR EACH SLAVE
				for l_slave in self._slave_addresses_list: 
					self._sit_modbus_registers = OrderedDict()
					try:
						self._init_sit_modbus_registers(l_slave)
						self.read_all_sit_modbus_registers()
						if self._args.store_values:
							self.store_values_into_csv(self._sit_modbus_registers, l_slave)
						if self._args.display_all:
							print(self.out_human_readable(a_with_description=self._args.long))
						if self._args.raise_event:
							assert len(self._sit_modbus_registers) > 0, 'modbus_registers_not_empty'
							self.call_sit_modbus_registers_events()
						if self._args.test:
							self.test()
					except ModbusException as l_e:
						self._logger.error('Modbus error on slave {}, msg:{}'.format(l_slave, l_e))
					except Exception as l_e:
						self._logger.error('Exception on slave {}, msg:{}'.format(l_slave, l_e))
						raise l_e

		except Exception as l_e:
			self._logger.exception("execute_corresponding_args-> Exception occured: %s" % (l_e))
			print('Error: %s' % (l_e))
			raise l_e
		finally:
			if self.is_connected():
				self.disconnect()
		self.invariants()


	def add_arg_parse(self):
		"""
		Override method
		"""
		self.add_arg_parse_modbus_device()
		self._parser.add_argument('-e', '--raise_event', help='Raises the corresponding event if setted', action="store_true")
		self._parser.add_argument('-c', '--slave_address', help='Slave address of modbus device', nargs='?', required=True)

	def add_required_named(self, a_required_named):
		pass

	def test(self):
		"""
			Test function
		"""
		try:
			self._logger.info ("################# BEGIN #################")
#			l_sit_dt = SitDateTime()
#			l_is_between_sunrise_sunset = l_sit_dt.now_is_into_sunrise_sunset_from_conf(self._sit_json_conf)
			#self.call_sit_modbus_registers_events(l_slave)
#			self._logger.info("--> ************* device models *************: %s" % (l_d.models))	 #Lists properties to be loaded with l_d.<property>.read() and then access them
#			self._logger.info("-->inverter ************* l_d.inverter.points *************: %s" % (l_d.inverter.points))	#Gives the inverter available properties
#			self._logger.info("-->inverter ************* common *************: %s" % (l_d.common))	
#			self._logger.info("-->inverter ************* common Serial Number *************: %s" % (l_d.common.SN))	
			self._logger.info ("################# END #################")
		except Exception as l_e:
			self._logger.exception("Exception occured: %s" % (l_e))
			print('Error: %s' % (l_e))
			self._logger.error('Error: %s' % (l_e))
			raise l_e

	def invariants(self):
		self.invariants_modbus_device()
		assert isinstance(self._slave_addresses_list, list) or self._slave_addresses_list is None, 'self._slave_address is list or None {}'.format(self._slave_addresses_list)
		for l_slave in self._slave_addresses_list:
			assert l_slave >=3, 'l_slave >=3 not the case:{}'.format(l_slave)

"""
Main method
"""
def main():
	#logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, filemode="a+", format="%(asctime)-15s %(levelname)-8s %(message)s")
	logger = logging.getLogger(__name__)

	try:
		l_obj = ClusterControllerInverter()
		l_obj.execute_corresponding_args()
#		l_id.test()
		pass
	except KeyboardInterrupt:
		logger.exception("Keyboard interruption")
	except Exception:
		logger.exception("Exception occured")


if __name__ == '__main__':
    main()
