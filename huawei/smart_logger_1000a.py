#!/usr/bin/env python3
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#       DESCRIPTION: 
#			huawei smart logger 1000a script to get data from modbus and store them into csv file
#
#            -h or --help for more informations about use
#
#			Logging into /var/log/solarity/file_name.log
#
#       CALL SAMPLE:
	#		/data/solarity/sit-raspi/sty-pub-raspi-modbus-drivers/huawei/smart_logger_1000a.py --host_ip '192.168.0.74' --host_mac '00:90:E8:73:0A:D6' --store_values --raise_event
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
#
#		*************************************************************************************************
#       @author: Philippe Gachoud
#       @creation: 20200614
#       @last modification:
#       @version: 1.0
#       @URL: $URL
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
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# INCLUDES
try:
	import sys
	import os, errno
	sys.path.append(os.path.join(os.path.dirname(__file__), '../lib')) #the way to import directories
	sys.path.append(os.path.join(os.path.dirname(__file__), '../lib/register_types')) #the way to import directories
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
	from register_type_int16_u import RegisterTypeInt16u
	from register_type_int16_s import RegisterTypeInt16s
	from register_type_int32_u import RegisterTypeInt32u
	from register_type_int32_s import RegisterTypeInt32s
	from register_type_int64_u import RegisterTypeInt64u
	from register_type_sma_cc_device_class import RegisterTypeSmaCCDeviceClass
	from sit_date_time import SitDateTime
	from sit_json_conf import SitJsonConf
	from sit_utils import SitUtils
	from sit_constants import SitConstants
except ImportError as l_err:
	print("ImportError: {0}".format(l_err))
	print(sys.path)
	raise l_err

class SmartLogger1000a(SitModbusDevice):

# CONSTANTS

	DEFAULT_SLAVE_ADDRESS = 1
	DEFAULT_MODBUS_PORT = 502
	DEFAULT_TARGET_MODE = SitModbusDevice.TARGET_MODE_TCP
	MIN_W_FOR_RAISE_EVENT_GENERATION = 2000
	PARSER_DESCRIPTION = 'Actions with Huawei smart logger 1000a device. ' + SitConstants.DEFAULT_HELP_LICENSE_NOTICE

# CLASS ATTRIBUTES

	_byte_order = Endian.Big
	_word_order = Endian.Big
	_substract_one_to_register_index = False

# FUNCTIONS DEFINITION 

	"""
		Initialize
	"""
	def __init__(self, a_slave_address=DEFAULT_SLAVE_ADDRESS, a_port=DEFAULT_MODBUS_PORT, an_ip_address=None):
		assert self.valid_slave_address(a_slave_address), 'invalid a_slave_address:{}'.format(a_slave_address)
		try:
			self.init_arg_parse()
			assert self.valid_slave_address(a_slave_address), 'a_slave_address parameter invalid:{}'.format(l_slave_address)
			l_slave_address = a_slave_address
			if __name__ == '__main__':
				if (hasattr(self._args, 'slave_address') and self._args.slave_address):
					l_slave_address = self._args.slave_address
			super().__init__(l_slave_address, self.DEFAULT_TARGET_MODE, a_port=self.DEFAULT_MODBUS_PORT, an_ip_address=self._args.host_ip) 
			self._logger = SitLogger().new_logger(self.__class__.__name__, self._args.host_mac)
			self._init_sit_modbus_registers(l_slave_address)

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
		assert self.valid_slave_address(a_slave_address), 'invalid a_slave_address:{}'.format(a_slave_address)
		self.add_common_sit_modbus_registers(1)

		self.invariants()


	def add_common_sit_modbus_registers(self, a_slave_address):
		"""
		Common devices registers
		"""
		assert self.valid_slave_address(a_slave_address), 'invalid a_slave_address:{}'.format(a_slave_address)
		assert a_slave_address == 1 or a_slave_address >= 3, 'Dont ask for slave_address 2, the add_cc_only_sit_modbus_registers is done for that! addr:{}'.format(a_slave_address)

		l_reg_list = OrderedDict()
		l_slave_address = a_slave_address
		SitUtils.od_extend(l_reg_list, RegisterTypeInt32s('W', 'Total active output power of all inverters', 40525, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'kW', an_is_metadata=False))

		#SitUtils.od_extend(l_reg_list, RegisterTypeStrVar('Mn', 'Model', 30000, 15, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'String15', an_is_metadata=True))

		# CLUSTER AND INVERTERS
#		SitUtils.od_extend(l_reg_list, RegisterTypeInt32u('Vr', 'Version number of the SMA Modbus profile', 30001, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'Int32u', an_is_metadata=True))
#		
#		SitUtils.od_extend(l_reg_list, RegisterTypeInt32u('ID', 'SUSy ID (of the Cluster Controller)', 30003, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'Int32u', an_is_metadata=True))
#		SitUtils.od_extend(l_reg_list, RegisterTypeInt32u('SN', 'Serial number (of the Cluster Controller)', 30005, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'Int32u', an_is_metadata=True))
#		SitUtils.od_extend(l_reg_list, RegisterTypeInt32s('NewData', 'Modbus data change: meter value is increased by the Cluster Controller if new data is available.', 30007, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'Int32u', an_is_metadata=False))
#		SitUtils.od_extend(l_reg_list, RegisterTypeSmaCCDeviceClass('DeviceClass', 'Device Class', 30051, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'Enum', an_is_metadata=True))
#
#		SitUtils.od_extend(l_reg_list, RegisterTypeInt32s('W', 'Current active power on all line conductors (W), accumulated values of the inverters', 30775, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'W', an_is_metadata=False, an_event=SitModbusRegisterEvent(self._W_event)))
#		SitUtils.od_extend(l_reg_list, RegisterTypeInt64u('Wh', 'Total energy fed in across all line conductors, in Wh (accumulated values of the inverters) System param', 30513, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'Wh', an_is_metadata=False))
#		SitUtils.od_extend(l_reg_list, RegisterTypeInt32s('VAr', 'Reactive power on all line conductors (var), accumulated values of the inverters', 30805, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'VAr', an_is_metadata=False))
#		SitUtils.od_extend(l_reg_list, RegisterTypeInt64u('TotWhDay', 'Energy fed in on current day across all line conductors, in Wh (accumulated values of the inverters)', 30517, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'Wh', an_is_metadata=False))
#
		self.append_modbus_registers(l_reg_list)


	def _W_event(self, a_sit_modbus_register):
		"""
		Called by modbus_device.call_sit_modbus_registers_events()
		"""
		self._logger.debug('_W_event-> register:{}'.format(a_sit_modbus_register.out_short()))
		l_short_desc = 'W'
		l_min_val = self.MIN_W_FOR_RAISE_EVENT_GENERATION
		l_val = a_sit_modbus_register.value 
		l_sit_dt = SitDateTime()

		if a_sit_modbus_register.short_description == l_short_desc:
			l_start_time = time(8, 30)
			l_end_time = time(16, 30)
			l_is_day, l_valid_time = l_sit_dt.time_is_between(datetime.now().time(), l_start_time, l_end_time)
#			l_is_between_sunrise_sunset = l_sit_dt.now_is_into_sunrise_sunset_from_conf(self._sit_json_conf)
#
#			self._logger.debug('read_sit_modbus_register-> l_is_day:{} l_valid_time:{} l_is_between_sunrise_sunset:{}'.format(l_is_day, l_valid_time, l_is_between_sunrise_sunset))
			l_msg = '_W_event-> register_index:{} value ({}) '.format(a_sit_modbus_register.register_index, l_val)
			l_msg += ' between {} and {}'.format(l_start_time, l_end_time)
			self._logger.info('_W_event-> DEVICE IS GENERATING {} kW'.format(l_val))
			if ( l_valid_time and
					l_val <= l_min_val):
				l_msg = '_W_event-> register_index:{} value ({} <= {}), valid_time:{}'.format(a_sit_modbus_register.register_index, l_val, l_min_val, l_valid_time)
				self._logger.warning(l_msg)
				# Create Dir
				l_dir = '/tmp/solarity_events'
				if not os.path.exists(l_dir):
					os.makedirs(l_dir)
				l_file = self.__class__.__name__ + '_event_{}_register_{}_slave_{}'.format(datetime.now().strftime("%Y%m%d_%H"), a_sit_modbus_register.register_index, a_sit_modbus_register.slave_address)
				l_file_abs_path = l_dir + '/' + l_file
				if not os.path.exists(l_file_abs_path):
					self._logger.info('_W_event-> Event not sent, sending email file:{}'.format(l_file_abs_path))
					# SEND MAIL
					l_subject = 'event with failure on $(hostname) slave:' + str(a_sit_modbus_register.slave_address) + ' $(date +%Y%m%d_%H%M%S) W val:(' + str(l_val) + ' <= ' + str(l_min_val) + ')W '
					l_body = ['event in slave:{} with failure on $(hostname) $(date +%Y%m%d_%H%M%S) review file {}'.format(a_sit_modbus_register.slave_address, self.csv_file_path(a_sit_modbus_register.slave_address))]
					l_body.append(' Between {} and {}'.format(l_start_time, l_end_time))
					l_body.append('Register->out:{}'.format(a_sit_modbus_register.out_human_readable(a_with_description=self._args.long)))
					l_subject, l_body = self._setted_parts(l_subject, l_body)
					SitUtils.send_mail(self.events_mail_receivers(), l_subject, l_body, [self.csv_file_path(a_sit_modbus_register.slave_address)])

					os.mknod(l_file_abs_path)
				else:
					self._logger.warning('_W_event-> Event already sent, not sending email file:{}'.format(l_file_abs_path))

			else:
				l_msg = '_W_event-> Event not raised register_index:{} value ({} > {}), valid_time:{}'.format(a_sit_modbus_register.register_index, l_val, l_min_val, l_valid_time)
				self._logger.debug(l_msg)

	def _setted_parts(self, a_subject, a_body):
		return a_subject, a_body

	def manual_restart(self):
		"""
		Manual restart 
		documented on p.45 of doc
		"""
		l_res = 'test_res'
		self._logger.info('manual_restart-> NOW')
		#a_register_index, a_slave_address, a_value):
		l_res = self.write_register_value(0, 201, 1)
		self._logger.info('manual_restart-> result:{}'.format(l_res))

		return l_res

	def read_all_sit_modbus_registers(self): 
		"""
		Read inverters data
		"""
		super().read_all_sit_modbus_registers()

#		l_reg_index = 42109
#		l_slave_address = 3
#		self.read_inverter_data(l_slave_address)
	
	def read_inverter_data(self, a_slave_address):
		"""
		Was for test but not working
		"""
		assert False, 'deprecated'
		l_reg = RegisterTypeInt64u('Wh2', 'Total energy fed in across all line conductors, in Wh (accumulated values of the inverters) System param', 30513, SitModbusRegister.ACCESS_MODE_R, 'Wh', an_is_metadata=False, a_slave_address=a_slave_address)
		self.read_inverter_data_register(l_reg, a_slave_address)
		print (l_reg.out_human_readable(a_with_description=True))

#		l_reg = RegisterTypeInt32u('SN', 'Serial Number', a_reg_index + 1, SitModbusRegister.ACCESS_MODE_R, 'Int32u', an_is_metadata=True)
#		self.read_inverter_data_register(l_reg, a_slave_address)
#
#		l_reg = RegisterTypeInt16u('UnitID', 'Unit ID', a_reg_index + 3, SitModbusRegister.ACCESS_MODE_R, 'Int32u', an_is_metadata=True)
#		self.read_inverter_data_register(l_reg, a_slave_address)


	def read_inverter_data_register(self, a_register, a_slave_address):
		"""
		Reads given inverter data
		Was for test but not working
		"""
		assert False, 'deprecated'
		try:
			self.read_sit_modbus_register(a_register, a_slave_address)
			if self._args.store_values:
				pass
	#			self.store_values_into_csv([l_reg], l_slave)
			if self._args.display_all:
				print('***************** INVERTER slave:{} ******************'.format(a_slave_address))
				print(a_register.out_human_readable(a_with_description=self._args.long))
		except ModbusException as l_e:
			self._logger.error('read_inverter_data-> error reading register {}'.format(l_e))
		except Exception as l_e:
			raise l_e

# ACCESS


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
				assert self.valid_slave_address(self._slave_address), 'Invalid slave address {}'.format(self._slave_address)
				self.read_all_sit_modbus_registers()
				if self._args.store_values:
					self.store_values_into_csv(self._sit_modbus_registers, self._slave_address)
				if self._args.display_all:
					print(self.out_human_readable(a_with_description=self._args.long))
				if self._args.raise_event:
					assert len(self._sit_modbus_registers) > 0, 'modbus_registers_not_empty'
					self.call_sit_modbus_registers_events()
				if self._args.test:
					self.test()
#			if self._args.manual_restart:
#				self.manual_restart()
		except Exception as l_e:
			self._logger.exception("execute_corresponding_args-> Exception occured: %s" % (l_e))
			print('Error: %s' % (l_e))
			raise l_e
		finally:
			if self.is_connected():
				self.disconnect()
		self.invariants()

	def add_arg_parse_modbus_device(self):
		super().add_arg_parse()

	def add_arg_parse(self):
		"""
		Override method
		"""
		self.add_arg_parse_modbus_device()
		self._parser.add_argument('-e', '--raise_event', help='Raises the corresponding event if setted', action="store_true")
		#self._parser.add_argument('-r', '--manual_restart', help='Sends a manual restart to inverter manager', action="store_true")
		self._parser.add_argument('-c', '--slave_address', help='Slave address of modbus device', nargs='?')

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

	def events_mail_receivers(self):
		return ['devices_events@solarityenergia.com', 'operaciones@solarityenergia.com']
		#return ['devices_events@solarityenergia.com']
		#return ['philippe@solarityenergia.com', 'ph.gachoud@gmail.com']

	def invariants_modbus_device(self):
		super().invariants()

	def invariants(self):
		self.invariants_modbus_device()

"""
Main method
"""
def main():
	#logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, filemode="a+", format="%(asctime)-15s %(levelname)-8s %(message)s")
	logger = logging.getLogger(__name__)

	try:
		l_obj = SmartLogger1000a()
		l_obj.execute_corresponding_args()
#		l_id.test()
		pass
	except KeyboardInterrupt:
		logger.exception("Keyboard interruption")
	except Exception:
		logger.exception("Exception occured")


if __name__ == '__main__':
    main()
