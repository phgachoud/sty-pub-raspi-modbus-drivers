#!/usr/bin/env python3
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#       DESCRIPTION: 
#
#       CALL SAMPLE:
#			/data/solarity/sit-raspi/sty-pub-raspi-modbus-drivers/sma/inverter_manager.py --host_ip '192.168.0.74' --host_mac '00:90:E8:73:0A:D6' --store_values --raise_event
#	
#	
#		REQUIRE
#			sudo apt-get install python3-serial or sudo apt-get install python-serial
#			sunspec dependency: git submodule update --init --recursive
#			sudo apt install python3-pip
#			sudo pip3 install serial #in case of error unsupported operand type(s) for -=: 'Retry' and 'int' sudo pip3 install --upgrade setuptools
#
#
#		*************************************************************************************************
#       @author: Philippe Gachoud
#       @creation: 20200403
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
#
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# INCLUDES
try:
	import sys
	import os, errno
	sys.path.append(os.path.join(os.path.dirname(__file__), '../lib')) #the way to import directories
	sys.path.append(os.path.join(os.path.dirname(__file__), '../lib/register_types')) #the way to import directories
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
	from register_type_string8 import RegisterTypeString8
	from register_type_string16 import RegisterTypeString16
	from register_type_int16_u_scale_factor import RegisterTypeInt16uScaleFactor
	from register_type_int32_u_scale_factor import RegisterTypeInt32uScaleFactor
	from sit_date_time import SitDateTime
	from sit_json_conf import SitJsonConf
	from sit_utils import SitUtils
	from sit_constants import SitConstants
except ImportError as l_err:
	print("ImportError: {0}".format(l_err))
	raise l_err

class InverterManager(SitModbusDevice):

# CONSTANTS

	DEFAULT_SLAVE_ADDRESS = 125
	DEFAULT_MODBUS_PORT = 502
	DEFAULT_TARGET_MODE = SitModbusDevice.TARGET_MODE_TCP
	MIN_W_FOR_RAISE_EVENT_GENERATION = 1000
	PARSER_DESCRIPTION = 'Actions with sma inverter manager. ' + SitConstants.DEFAULT_HELP_LICENSE_NOTICE

# CLASS ATTRIBUTES

	_byte_order = Endian.Big
	_word_order = Endian.Big
	_substract_one_to_register_index = True
	_slave_addresses_list = None

# FUNCTIONS DEFINITION 

	"""
		Initialize
	"""
	def __init__(self, a_slave_address=DEFAULT_SLAVE_ADDRESS, a_port=DEFAULT_MODBUS_PORT, an_ip_address=None):
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

			super().__init__(l_slave_address, self.DEFAULT_TARGET_MODE, a_port=self.DEFAULT_MODBUS_PORT, an_ip_address=self._args.host_ip) 
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
		l_reg_list = OrderedDict()
		l_slave_address = a_slave_address

		self._add_common_registers(l_reg_list, l_slave_address)

		SitUtils.od_extend(l_reg_list, RegisterTypeInt16u('ID', 'Model ID (ID): 120 = Sunspec nameplate model', 40238, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'uint16', an_is_metadata=True))
		SitUtils.od_extend(l_reg_list, RegisterTypeInt16uScaleFactor('AC_A', 'AC Current sum of all inverters', 40188, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'A', a_scale_factor=40192))

		SitUtils.od_extend(l_reg_list, RegisterTypeInt16u('VArPct_Mod', 'Mode of the percentile reactive power limitation: 1 = in % of WMax', 40365, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'enum16'))
		SitUtils.od_extend(l_reg_list, RegisterTypeInt16u('VArPct_Ena', 'Control of the percentile reactive power limitation,(SMA: Qext): 1 = activated', 40365, l_slave_address, SitModbusRegister.ACCESS_MODE_RW, 'enum16'))

		SitUtils.od_extend(l_reg_list, RegisterTypeInt16u('WMaxLim_Ena', 'Limiting (0 Deactivate, 1 activated):', 40353, l_slave_address, SitModbusRegister.ACCESS_MODE_RW, 'enum16'))
		SitUtils.od_extend(l_reg_list, RegisterTypeInt16uScaleFactor('WMaxLimPct', 'Set power to default value, in % of WMax-WMaxLimPct_SF', 40349, l_slave_address, SitModbusRegister.ACCESS_MODE_RW, 'uint16', a_scale_factor=40367))

		SitUtils.od_extend(l_reg_list, RegisterTypeInt16uScaleFactor('VRef', 'Voltage at the PCC (VRef), in V VRef_SF (40289)', 40269, l_slave_address, SitModbusRegister.ACCESS_MODE_RW, 'uint16', 40289))
		SitUtils.od_extend(l_reg_list, RegisterTypeInt16uScaleFactor('VMax', 'Set value for maximum voltage (VMax), in V VMinMax_SF', 40271, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'uint16', a_scale_factor=40291))

		self.append_modbus_registers(l_reg_list)

		self.invariants()


	def _add_common_registers(self, a_reg_list, a_slave_address):
		"""
		adds to a_reg_list
		"""
		l_reg_list = a_reg_list
		l_slave_address = a_slave_address

		SitUtils.od_extend(l_reg_list, RegisterTypeString16('Mn', 'Manufacturer', 40005, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'String16', an_is_metadata=True))
		SitUtils.od_extend(l_reg_list, RegisterTypeString16('Md', 'Model (Md): SMA Inverter Manager', 40021, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'String16', an_is_metadata=True))
		SitUtils.od_extend(l_reg_list, RegisterTypeString8('Opt', 'Options (Opt): Inverter Manager name', 40037, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'String8', an_is_metadata=True))
		SitUtils.od_extend(l_reg_list, RegisterTypeString8('Vr', 'Version (Vr): Version number of the installed firmware', 40045, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'String8', an_is_metadata=True))
		SitUtils.od_extend(l_reg_list, RegisterTypeString16('SN', 'Serial number (SN) of the device that uses the Modbus unit ID', 40053, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'String16', an_is_metadata=True))

		SitUtils.od_extend(l_reg_list, RegisterTypeInt16uScaleFactor('PPVphAB', 'Voltage, line conductor L1 to L2, in V V_SF (40199) : average value of all inverters', 40193, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'V', a_scale_factor=40199))
		SitUtils.od_extend(l_reg_list, RegisterTypeInt16uScaleFactor('PPVphBC', 'Voltage, line conductor L2 to L3, in V V_SF (40199) : average value of all inverters', 40194, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'V', a_scale_factor=40199))
		SitUtils.od_extend(l_reg_list, RegisterTypeInt16uScaleFactor('PPVphCA', 'Voltage, line conductor L3 to L1, in V V_SF (40199) : average value of all inverters', 40195, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'V', a_scale_factor=40199))

		SitUtils.od_extend(l_reg_list, RegisterTypeInt16uScaleFactor('PPVphA', 'Voltage, line conductor L1 to N (PPVphA), in V-V_SF (40199): average value of all inverters', 40196, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'V', a_scale_factor=40199))
		SitUtils.od_extend(l_reg_list, RegisterTypeInt16uScaleFactor('PPVphB', 'Voltage, line conductor L1 to N (PPVphB), in V-V_SF (40199): average value of all inverters', 40197, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'V', a_scale_factor=40199))
		SitUtils.od_extend(l_reg_list, RegisterTypeInt16uScaleFactor('PPVphC', 'Voltage, line conductor L1 to N (PPVphC), in V-V_SF (40199): average value of all inverters', 40198, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'V', a_scale_factor=40199))

		SitUtils.od_extend(l_reg_list, RegisterTypeInt16uScaleFactor('W', 'Active power (W), in W-W_SF (40201): sum of all inverters', 40200, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'W', a_scale_factor=40192, an_event=SitModbusRegisterEvent(self._W_event), a_post_set_value_call=self.w_fix))
		SitUtils.od_extend(l_reg_list, RegisterTypeInt32uScaleFactor('WH', 'Total yield (WH), in Wh WH_SF (40212): sum of all inverters', 40210, l_slave_address, SitModbusRegister.ACCESS_MODE_R, 'WH', a_scale_factor=40212))
		SitUtils.od_extend(l_reg_list, RegisterTypeInt16uScaleFactor('TmpCab', 'Internal temperature, in °C Tmp_SF (40223): average value of all inverters', 40219, l_slave_address, SitModbusRegister.ACCESS_MODE_R, '°C', a_scale_factor=40223))






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
					l_subject = 'event with failure on $(hostname) ' + str(a_sit_modbus_register.slave_address) + ' $(date +%Y%m%d_%H%M%S) W val:(' + str(l_val) + ' <= ' + str(l_min_val) + ')kW '
					l_body = ['event in slave:{} with failure on $(hostname) $(date +%Y%m%d_%H%M%S) review file {}'.format(a_sit_modbus_register.slave_address, self.csv_file_path(a_sit_modbus_register.slave_address))]
					l_body.append(' Between {} and {}'.format(l_start_time, l_end_time))
					l_body.append('Register->out:{}'.format(a_sit_modbus_register.out_human_readable(a_with_description=self._args.long)))
					SitUtils.send_mail(self.events_mail_receivers(), l_subject, l_body, [self.csv_file_path(a_sit_modbus_register.slave_address)])

					os.mknod(l_file_abs_path)
				else:
					self._logger.warning('_W_event-> Event already sent, not sending email file:{}'.format(l_file_abs_path))

			else:
				l_msg = '_W_event-> Event not raised register_index:{} value ({} > {}), valid_time:{}'.format(a_sit_modbus_register.register_index, l_val, l_min_val, l_valid_time)
				self._logger.debug(l_msg)

	def w_fix(self, a_sit_modbus_register):
		"""
		"""
		l_new_val = a_sit_modbus_register.value * 100
		self._logger.debug('w_fix->Setting new value-> old:{} new:{}'.format(a_sit_modbus_register.value, l_new_val))
		a_sit_modbus_register.value = l_new_val

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
				assert self.valid_slave_address_list(self._slave_addresses_list), 'Slave addresses list is invalid:{}'.format(self._slave_addresses_list)
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
			if self._args.manual_restart:
				self.manual_restart()
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
		self._parser.add_argument('-r', '--manual_restart', help='Sends a manual restart to inverter manager', action="store_true")
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
		l_obj = InverterManager()
		l_obj.execute_corresponding_args()
#		l_id.test()
		pass
	except KeyboardInterrupt:
		logger.exception("Keyboard interruption")
	except Exception:
		logger.exception("Exception occured")


if __name__ == '__main__':
    main()
