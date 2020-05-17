#!/usr/bin/env python3
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#       DESCRIPTION: 
#
#       CALL SAMPLE:
#			~/data/solarity/sit-raspi/modbus/direct_marketing_interface.py --host_ip '192.168.0.34' --host_mac '00:90:E8:7B:76:9C' -v -t	
#	
#	REQUIRE
#
#       CALL PARAMETERS:
#               1) 
#
#       @author: Philippe Gachoud
#       @creation: 20200408
#       @last modification:
#       @version: 1.0
#       @URL: $URL
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# INCLUDES
try:
	import sys
	import os, errno
	sys.path.append(os.path.join(os.path.dirname(__file__), '../lib')) #the way to import directories
	from sit_logger import SitLogger
	from pymodbus.constants import Endian
	from sit_modbus_device import SitModbusDevice #from file_name import ClassName
	from sit_modbus_register import SitModbusRegister
	from inverter_manager import InverterManager
	#import sitmodbus#, SitModbusRegister
	import logging # http://www.onlamp.com/pub/a/python/2005/06/02/logging.html
	from logging import handlers
	import argparse
	#sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pysunspec'))
	from datetime import datetime, date, time, timedelta
except ImportError as l_err:
	print("ImportError: {0}".format(l_err))
	raise l_err

class DirectMarketerInterface(InverterManager):

# CONSTANTS

	DEFAULT_SLAVE_ADDRESS = 200

# CLASS ATTRIBUTES

# FUNCTIONS DEFINITION 

	"""
		Initialize
	"""
	def __init__(self, a_slave_address=DEFAULT_SLAVE_ADDRESS):
		try:
			self.init_arg_parse()
			l_slave_address = self.DEFAULT_SLAVE_ADDRESS
			if self._args.slave_address:
				if self.valid_slave_address(self._args.slave_address):
					self._slave_address = int(self._args.slave_address)
			#self, a_slave_address=DEFAULT_SLAVE_ADDRESS, a_port=DEFAULT_MODBUS_PORT, an_ip_address=None
			super().__init__(l_slave_address, a_port=self.DEFAULT_MODBUS_PORT, an_ip_address=self._args.host_ip) 
			self._logger = SitLogger().new_logger(__name__, self._args.host_mac)
			self._init_sit_modbus_registers()
			#self._logger.debug('init->' + self.out())
		except OSError as l_e:
			self._logger.warning("init-> OSError, probably rollingfileAppender" % (l_e))
			if e.errno != errno.ENOENT:
				raise l_e
		except Exception as l_e:
			print('Error in init: %s' % (l_e))
			raise l_e
			#exit(1)

	def _init_sit_modbus_registers(self):
		"""
			Initializes self._sit_modbus_registers
		"""
		#	P.44 of doc
		self.add_modbus_register('OutLimitPerc', 'Specified output limitation through direct marketer n% (0-10000)', 1, SitModbusRegister.REGISTER_TYPE_INT_16, SitModbusRegister.ACCESS_MODE_RW, 'uint16')
		self.add_modbus_register('OutLimitPercMan', 'Manual output limitation that has been set via Sunspec Modbus', 2, SitModbusRegister.REGISTER_TYPE_INT_16, SitModbusRegister.ACCESS_MODE_R, 'uint16')
		self.add_modbus_register('OutLimitPercIoBox', 'Output limitation through the electric utility company that has been set via the IO box.', 3, SitModbusRegister.REGISTER_TYPE_INT_16, SitModbusRegister.ACCESS_MODE_R, 'uint16')
		self.add_modbus_register('OutLimitMin', 'Minimum of all output limitations. The nominal PV system power is derated to this value.', 4, SitModbusRegister.REGISTER_TYPE_INT_16, SitModbusRegister.ACCESS_MODE_R, 'uint16')
#		self.add_modbus_register('Md', 'Model (Md): SMA Inverter Manager', 40021, SitModbusRegister.REGISTER_TYPE_STRING_16, SitModbusRegister.ACCESS_MODE_R, 'String16')
#		self.add_modbus_register('Opt', 'Options (Opt): Inverter Manager name', 40037, SitModbusRegister.REGISTER_TYPE_STRING_8, SitModbusRegister.ACCESS_MODE_R, 'String8')
#		self.add_modbus_register('Vr', 'Version (Vr): Version number of the installed firmware', 40045, SitModbusRegister.REGISTER_TYPE_STRING_8, SitModbusRegister.ACCESS_MODE_R, 'String8')
#		self.add_modbus_register('SN', 'Serial number (SN) of the device that uses the Modbus unit ID', 40053, SitModbusRegister.REGISTER_TYPE_STRING_16, SitModbusRegister.ACCESS_MODE_R, 'String16')
#		self.add_modbus_register('PPVphA', 'Voltage, line conductor L1 to N (PPVphA), in V-V_SF (40199): average value of all inverters', 40196, SitModbusRegister.REGISTER_TYPE_INT_16, SitModbusRegister.ACCESS_MODE_R, 'V', 40199)
#		self.add_modbus_register('AC_A', 'AC Current sum of all inverters', 40188, SitModbusRegister.REGISTER_TYPE_INT_16, SitModbusRegister.ACCESS_MODE_R, 'A', 40192)
#		self.add_modbus_register('W', 'Active power (W), in W-W_SF (40201): sum of all inverters', 40200, SitModbusRegister.REGISTER_TYPE_INT_16, SitModbusRegister.ACCESS_MODE_R, 'W', 40192)
#		self.add_modbus_register('WH', 'Total yield (WH), in Wh WH_SF (40212): sum of all inverters', 40210, SitModbusRegister.REGISTER_TYPE_INT_32, SitModbusRegister.ACCESS_MODE_R, 'WH', 40212)
#		self.add_modbus_register('TmpCab', 'Internal temperature, in °C Tmp_SF (40223): average value of all inverters', 40219, SitModbusRegister.REGISTER_TYPE_INT_16, SitModbusRegister.ACCESS_MODE_R, '°C', 40223)
#		self.add_modbus_register('ID', 'Model ID (ID): 120 = Sunspec nameplate model', 40238, SitModbusRegister.REGISTER_TYPE_INT_16, SitModbusRegister.ACCESS_MODE_R, 'uint16')
#		self.add_modbus_register('VArPct_Mod', 'Mode of the percentile reactive power limitation: 1 = in % of WMax', 40365, SitModbusRegister.REGISTER_TYPE_ENUM_16, SitModbusRegister.ACCESS_MODE_R, 'enum16')
#		self.add_modbus_register('VArPct_Ena', 'Control of the percentile reactive power limitation,(SMA: Qext): 1 = activated', 40365, SitModbusRegister.REGISTER_TYPE_ENUM_16, SitModbusRegister.ACCESS_MODE_RW, 'enum16')

	def init_arg_parse(self):
		"""
			Parsing arguments
		"""
		self._parser = argparse.ArgumentParser(description='Actions with Inverter Manager through TCP')
		self._parser.add_argument('-v', '--verbose', help='increase output verbosity', action="store_true")
		self._parser.add_argument('-t', '--test', help='Runs test method', action="store_true")
		self._parser.add_argument('-u', '--slave_address', help='Slave address of modbus device', nargs='?')

		#self._parser.add_argument('-u', '--base_url', help='NOT_IMPLEMENTED:Gives the base URL for requests actions', nargs='?', default=self.DEFAULT_BASE_URL)
		l_required_named = self._parser.add_argument_group('required named arguments')
		l_required_named.add_argument('-i', '--host_ip', help='Host IP', nargs='?', required=True)
		l_required_named.add_argument('-m', '--host_mac', help='Host MAC', nargs='?', required=True)
#		l_required_named.add_argument('-l', '--longitude', help='Longitude coordinate (beware timezone is set to Chile)', nargs='?', required=True)
#		l_required_named.add_argument('-a', '--lattitude', help='Lattitude coordinate (beware timezone is set to Chile)', nargs='?', required=True)
#		l_required_named.add_argument('-d', '--device_type', help='Device Type:' + ('|'.join(str(l) for l in self.DEVICE_TYPES_ARRAY)), nargs='?', required=True)
		l_args = self._parser.parse_args()
		self._args = l_args

# ACCESS


# IMPLEMENTATION


# EXECUTE ARGS

	"""
		Parsing arguments and calling corresponding functions
	"""
	def execute_corresponding_args(self):
		if self._args.verbose:
			self._logger.setLevel(logging.DEBUG)
		else:
			self._logger.setLevel(logging.DEBUG)
		if self._args.test:
			self.test()

		#if self._args.store_values:

	"""
		Test function
	"""
	def test(self):
		try:
			self.connect()
			self.read_all_sit_modbus_registers()
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
		finally:
			self.disconnect()


"""
Main method
"""
def main():
	#logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, filemode="a+", format="%(asctime)-15s %(levelname)-8s %(message)s")
	logger = logging.getLogger(__name__)

	try:
		l_obj = DirectMarketerInterface()
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
