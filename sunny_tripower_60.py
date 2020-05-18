#!/usr/bin/env python3
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#       DESCRIPTION: 
#
#       CALL SAMPLE:
#
#			#Crontab
#			* 5-23 * * * sleep 10;~/data/solarity/sit-raspi/modbus/sunny_tripower_60.py --host_ip '192.168.0.74' --host_mac '00:90:E8:73:0A:D6' --store_values --raise_event --slave_address 126 > /dev/null
#			* 5-23 * * * sleep 20;~/data/solarity/sit-raspi/modbus/sunny_tripower_60.py --host_ip '192.168.0.74' --host_mac '00:90:E8:73:0A:D6' --store_values --raise_event --slave_address 127 > /dev/null
#			* 5-23 * * * sleep 30;~/data/solarity/sit-raspi/modbus/sunny_tripower_60.py --host_ip '192.168.0.74' --host_mac '00:90:E8:73:0A:D6' --store_values --raise_event --slave_address 128 > /dev/null
#	
#	REQUIRE
#		sudo mkdir /var/log/solarity;sudo chmod -R 777 /var/log/solarity
#		sudo mkdir /var/solarity;sudo chmod -R 777 /var/solarity
#		sudo mkdir /etc/opt/solarity;sudo chmod -R 777 /etc/opt/solarity
#
#       CALL PARAMETERS:
#               1) 
#
#       @author: Philippe Gachoud
#       @creation: 20200403
#       @last modification:
#       @version: 1.0
#       @URL: $URL
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# INCLUDES
try:
	import sys
	import os, errno
	sys.path.append(os.path.join(os.path.dirname(__file__), '../lib')) #the way to import directories
	sys.path.append(os.path.join(os.path.dirname(__file__), '../lib/register_types')) #the way to import directories
	from collections import OrderedDict
	from sit_logger import SitLogger
	from pymodbus.constants import Endian
	from pymodbus.exceptions import ModbusException

	from sit_modbus_device import SitModbusDevice #from file_name import ClassName
	from sit_modbus_register import SitModbusRegister
	from inverter_manager import InverterManager
	from register_type_int16_u import RegisterTypeInt16u
	from register_type_int16_s import RegisterTypeInt16s
	from register_type_int32_u import RegisterTypeInt32u
	from register_type_int32_s import RegisterTypeInt32s
	from register_type_int64_u import RegisterTypeInt64u
	from register_type_string8 import RegisterTypeString8
	from register_type_string16 import RegisterTypeString16
	from register_type_int16_u_scale_factor import RegisterTypeInt16uScaleFactor
	from register_type_int32_u_scale_factor import RegisterTypeInt32uScaleFactor

	from sit_modbus_register_event import SitModbusRegisterEvent
	from sit_utils import SitUtils

	import logging # http://www.onlamp.com/pub/a/python/2005/06/02/logging.html
	from logging import handlers
	import argparse
	#sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pysunspec'))
	from datetime import datetime, date, time, timedelta
except ImportError as l_err:
	print("ImportError: {0}".format(l_err))
	raise l_err

class SunnyTripower60(InverterManager):

# CONSTANTS

	DEFAULT_SLAVE_ADDRESS = 126
	MIN_KW_FOR_RAISE_EVENT_GENERATION = 5

# FUNCTIONS DEFINITION 

	"""
		Initialize
	"""
	def __init__(self, a_slave_address=DEFAULT_SLAVE_ADDRESS):
		assert self.valid_slave_address(a_slave_address), 'init invalid slave address'
		try:
			self.init_arg_parse()
			l_slave_address = a_slave_address
			if (hasattr(self._args, 'slave_address') and self._args.slave_address):
				self._slave_addresses_list = SitUtils.args_to_list(self._args.slave_address)
			if self._slave_addresses_list is None:
				self._slave_addresses_list = [a_slave_address]

			assert self.valid_slave_address_list(self._slave_addresses_list), 'Given script arguments are not valid, or could not be parsed:{}'.format(self._slave_addresses_list)
			assert self.valid_ip(self._args.host_ip), 'valid ip address:{}'.format(self._args.host_ip)

			#a_slave_address=DEFAULT_SLAVE_ADDRESS, a_port=DEFAULT_MODBUS_PORT, an_ip_address=None
			super().__init__(l_slave_address, a_port=self.DEFAULT_MODBUS_PORT, an_ip_address=self._args.host_ip) 
			self._logger = SitLogger().new_logger(__name__, self._args.host_mac)
			#self._logger.debug('init->' + self.out())
		except OSError as l_e:
			self._logger.warning("init-> OSError, probably rollingfileAppender" % (l_e))
			if e.errno != errno.ENOENT:
				raise l_e
		except Exception as l_e:
			print('Error in init: %s' % (l_e))
			raise l_e
			#exit(1)
		self.invariants()

	def _init_sit_modbus_registers(self, a_slave_address):
		"""
			Initializes self._sit_modbus_registers
		"""
		assert len(self._sit_modbus_registers) == 0
		l_reg_list = OrderedDict()
		l_slave_address = a_slave_address

		self._add_common_registers(l_reg_list, l_slave_address)

		SitUtils.od_extend(l_reg_list, RegisterTypeInt16uScaleFactor('A', 'AC Current sum of all inverters', 40188, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'A', a_scale_factor=40192))

		self.append_modbus_registers(l_reg_list)

		#error self.add_modbus_register('ID', 'Model ID (ID): 120 = Sunspec nameplate model', 40238, SitModbusRegister.REGISTER_TYPE_INT_16_U, SitModbusRegister.ACCESS_MODE_R, 'uint16')
		#error self.add_modbus_register('VArPct_Mod', 'Mode of the percentile reactive power limitation: 1 = in % of WMax', 40365, SitModbusRegister.REGISTER_TYPE_ENUM_16, SitModbusRegister.ACCESS_MODE_R, 'enum16')
		#self.add_modbus_register('VArPct_Ena', 'Control of the percentile reactive power limitation,(SMA: Qext): 1 = activated', 40365, SitModbusRegister.REGISTER_TYPE_ENUM_16, SitModbusRegister.ACCESS_MODE_RW, 'enum16')
		self.invariants()


	"""
		Parsing arguments and calling corresponding functions
	"""
	def execute_corresponding_args(self):
		self.invariants()
		try:
			self.connect()
			if self._args.verbose:
				self._logger.setLevel(logging.DEBUG)
			else:
				self._logger.setLevel(logging.INFO)
			if (self._args.store_values or self._args.display_all or self._args.raise_event or self._args.test):
				assert self.valid_slave_address_list(self._slave_addresses_list), 'Slave addresses list is invalid:{}'.format(self._slave_addresses_list)
				# FOR EACH SLAVE
				for l_slave in self._slave_addresses_list: 
					self._sit_modbus_registers = OrderedDict()
					try:
						self._init_sit_modbus_registers(l_slave)
						assert len(self._sit_modbus_registers) > 0, 'modbusregisters empty'
						self.read_all_sit_modbus_registers()
						if self._args.store_values:
							self.store_values_into_csv(self._sit_modbus_registers, l_slave)
						if self._args.display_all:
							print(self.out_human_readable(a_with_description=self._args.long))
						if self._args.raise_event:
							self.call_sit_modbus_registers_events()
						if self._args.test:
							self.test()
					except ModbusException as l_e:
						self._logger.exception('execute_corresponding_args Exception:{}'.format(l_e), l_e)
						#pass it because of other slave addresses
					except Exception as l_e:
						self._logger.exception('execute_corresponding_args Exception:{}'.format(l_e), l_e)
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

	"""
		Test function
	"""
	def test(self):
		self.invariants()
		try:
			print ("################# BEGIN #################")
#			self._logger.info("--> ************* device models *************: %s" % (l_d.models))	 #Lists properties to be loaded with l_d.<property>.read() and then access them
#			self._logger.info("-->inverter ************* l_d.inverter.points *************: %s" % (l_d.inverter.points))	#Gives the inverter available properties
#			self._logger.info("-->inverter ************* common *************: %s" % (l_d.common))	
#			self._logger.info("-->inverter ************* common Serial Number *************: %s" % (l_d.common.SN))	
			print ("################# END #################")
		except Exception as l_e:
			self._logger.exception("Exception occured: %s" % (l_e))
			print('Error: %s' % (l_e))
			self._logger.error('Error: %s' % (l_e))
			raise l_e
		self.invariants()

	def invariants(self):
		self.invariants_modbus_device()  

"""
Main method
"""
def main():
	#logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, filemode="a+", format="%(asctime)-15s %(levelname)-8s %(message)s")
	logger = logging.getLogger(__name__)

	try:
		l_obj = SunnyTripower60()
		l_obj.execute_corresponding_args()
#		l_id.test()
		pass
	except KeyboardInterrupt:
		logger.exception("Keyboard interruption")
	except Exception as l_e:
		logger.exception("Exception occured")
		raise l_e


if __name__ == '__main__':
    main()
