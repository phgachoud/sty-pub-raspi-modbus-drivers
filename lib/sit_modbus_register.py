#!/usr/bin/env python3
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#       DESCRIPTION: Base modbus register, the idea is to inherit and redefine functions from this class
#	          see --help for using directly
#	          otherwise you can see children from this class like sma/cluster_controller.py
#
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
	import os.path
	import os, errno
	#sys.path.append(os.path.join(os.path.dirname(__file__), '../lib')) #the way to import directories
	from abc import ABC, abstractmethod
	from collections import OrderedDict
	import logging # http://www.onlamp.com/pub/a/python/2005/06/02/logging.html
	import argparse
	#sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pysunspec'))
	from datetime import datetime, date, time, timedelta
#	import jsonpickle # pip install jsonpickle
#	import json
	from sit_logger import SitLogger
	from sit_modbus_register_event import SitModbusRegisterEvent
except ImportError as l_err:
	print("ImportError: {0}".format(l_err))
	raise l_err

# GLOBAL CONSTANTS


class SitModbusRegister(ABC):

# CONSTANTS
	LOG_FILE_PATH = '/var/log/solarity'
	DEFAULT_LOGGING_LEVEL = logging.INFO #For console overrided by --verbose
	DEFAULT_FILE_LOGGING_LEVEL = logging.DEBUG #For file
	DEFAULT_CSV_FILE_LOCATION = '/var/solarity' #without ending slash


	DEFAULT_ACCESS_MODE='R'
	ACCESS_MODE_RW='RW'
	ACCESS_MODE_R='R'

# VARIABLES

	_logger = None

	_short_description = None
	_description = None
	_register_index = None
	_value = None
	_value_unit = None
	_access_mode = None
	_scale_factor_register_index = None
	_is_metadata = False
	_slave_address = None # Can be none, in that case the default slave_address is taken

	_words_count = None

	_event = None 
	_post_set_value_call = None

# FUNCTIONS DEFINITION 

	"""
		Initialize
	"""
	def __init__(
			self, 
			a_short_description, 
			a_description, 
			a_register_index, 
			a_slave_address, 
			an_access_mode=DEFAULT_ACCESS_MODE, 
			a_value_unit=None, 
			a_scale_factor_register_index=None, 
			an_event=None, 
			an_is_metadata=False, 
			a_post_set_value_call=None
		):
		#require
		assert self.valid_access_mode(an_access_mode), 'invalid an_access_mode:{}'.format(an_access_mode)
		assert self.valid_register_index(a_register_index), 'invalid a_register_index:{}'.format(a_register_index)
		from sit_modbus_device import SitModbusDevice
		assert SitModbusDevice.valid_slave_address(a_slave_address), 'invalid a_slave_address:{}'.format(a_slave_address)

		self._short_description = a_short_description
		self._description = a_description
		self._register_index = a_register_index
		self._access_mode = an_access_mode
		self._value_unit = a_value_unit
		self._scale_factor_register_index = a_scale_factor_register_index
		self._event = an_event
		self._is_metadata = an_is_metadata
		self._slave_address = a_slave_address
		self._post_set_value_call = a_post_set_value_call
	
		self._logger = SitLogger().new_logger(self.__class__.__name__)
		self._logger.debug('init-> created SitModbusRegister:%s' % (self.to_ordered_dict()))

		#ensure
		self.invariants()



	"""
		Parsing arguments
	"""
	def init_arg_parse(self):
		"""App help"""
		self._parser = argparse.ArgumentParser(description='Actions with sunspec through TCP')
		self._parser.add_argument('-v', '--verbose', help='increase output verbosity', action="store_true")
		self._parser.add_argument('-t', '--test', help='Runs test method', action="store_true")
		
		#self._parser.add_argument('-u', '--base_url', help='NOT_IMPLEMENTED:Gives the base URL for requests actions', nargs='?', default=self.DEFAULT_BASE_URL)
		l_required_named = self._parser.add_argument_group('required named arguments')
#		l_required_named.add_argument('-i', '--host_ip', help='Host IP', nargs='?', required=True)
#		l_required_named.add_argument('-u', '--slave_address', help='Slave address of modbus device', nargs='?', required=True)
#		l_required_named.add_argument('-l', '--longitude', help='Longitude coordinate (beware timezone is set to Chile)', nargs='?', required=True)
#		l_required_named.add_argument('-a', '--lattitude', help='Lattitude coordinate (beware timezone is set to Chile)', nargs='?', required=True)
#		l_required_named.add_argument('-d', '--device_type', help='Device Type:' + ('|'.join(str(l) for l in self.DEVICE_TYPES_ARRAY)), nargs='?', required=True)
		args = self._parser.parse_args()
		self._args = args

	"""
		Parsing arguments and calling corresponding functions
	"""
	def execute_corresponding_args( self ):
		self.init_arg_parse()
		if self._args.verbose:
			self._logger.setLevel(logging.DEBUG)
			self._console_handler.setLevel(logging.DEBUG)
			self._file_handler.setLevel(logging.DEBUG)
		else:
			self._logger.setLevel(logging.DEBUG)
			self._console_handler.setLevel(logging.ERROR)
			self._file_handler.setLevel(logging.DEBUG)
		if self._args.test:
			self.test()

		#if self._args.store_values:
	
# VALIDATION

	def valid_access_mode(self, v):
		"""
		Is  access mode valid
		"""
		return v == self.ACCESS_MODE_R or v == self.ACCESS_MODE_RW

	def valid_register_index(self, v):
		"""
		Value is int and > 0
		"""
		try:
			l_is_int = int(v)
			l_res = l_is_int > 0
		except Exception as l_e:
			l_res = False

		return l_res

	
# GETTERS AND SETTERS

	@property
	def short_description(self):
		return self._short_description
	
	@property
	def description(self):
		return self._description

	@property
	def	register_index(self):
		return self._register_index

	@property
	def value(self): 
		return self._value

	@value.setter
	def value(self, v):
		self._value = v

	def is_access_mode_rw(self):
		return self._access_mode == self.ACCESS_MODE_RW

	@property
	def value_unit(self):
		return self._value_unit

	@property
	def scale_factor_register_index(self):
		return self._scale_factor_register_index

	@property
	def is_metadata(self):
		return self._is_metadata

	@property
	def words_count(self): 
		return self._words_count

	@property
	def slave_address(self): 
		return self._slave_address

# STATUS REPORT

	def has_event(self):
		return self._event is not None

	def has_post_set_value_call(self):
		return self._post_set_value_call is not None
	
	def has_slave_address(self):
		from sit_modbus_device import SitModbusDevice
		return SitModbusDevice.valid_slave_address(self._slave_address)

# STATUS SETTING

	@abstractmethod
	def set_value_with_raw(self, v):
		# OR raise NotImplementedError
		pass

# EVENT

	def call_event(self):
		"""
			calls sit_event.call_method_to_call(self)
		"""
		assert self.has_event(), 'event not setted, check it before call'
		assert isinstance(self._event, SitModbusRegisterEvent), 'self._event is not a SitModbusRegister'

		self._logger.debug('call_event-> has_event:{}, register short_out:{}'.format(self.has_event(), self.out_short()))
		l_optional_args = None
		self._event.modbus_register = self
		#self._event.call_method_to_call([self, a_slave_address], l_optional_args)
		self._event.call_method_to_call([self], l_optional_args)


	def call_post_set_value(self):
		"""
			calls _post_set_value_call function
		"""
		assert self._post_set_value_call is not None, '_post_set_value_call is None'
		self._post_set_value_call(self)


# CONVERSION


# OUTPUT

	def to_ordered_dict(self):
		l_res = OrderedDict()

		l_res['short_description'] = self._short_description
		l_res['value'] = self._value
		l_res['value_unit'] = self._value_unit
		l_res['description'] = self._description
		l_res['register_index'] = self._register_index
		l_res['access_mode'] = self._access_mode
		l_res['scale_factor_register_index'] = self._scale_factor_register_index
		l_res['has_event'] = self.has_event()
		l_res['slave_address'] = self._slave_address

		return l_res

	def out(self, a_sep='|', an_item_prefix='', a_with_description=False):
		"""
			returns a string with values of to_ordered_dict()	
		"""
		l_res = ''
		for l_key, l_val in self.to_ordered_dict().items():
			l_res += an_item_prefix + l_key + ' = ' + str(l_val) + a_sep

		return l_res

	def out_short(self, a_sep='|'):
		"""
			returns a string with values of to_ordered_dict()	
		"""
		l_res = ''

		l_res = l_res + 'index:' + str(self._register_index) + a_sep
		l_res = l_res + 'short:' + self._short_description + a_sep
		l_res = l_res + 'desc:' + self._description + a_sep
		l_res = l_res + 'val:' + str(self._value) + a_sep
		l_res = l_res + 'u:' + str(self._value_unit) + a_sep
		l_res = l_res + 'has_event:' + str(self.has_event()) + a_sep
		l_res = l_res + 'slave:' + str(self._slave_address)

		return l_res

	def out_human_readable(self, an_item_prefix='', a_with_description=False):
		l_res = ''
		assert self.short_description is not None
		assert self.value_unit is not None
		l_val = self.value
		if l_val is None:
			l_val = 'None'
		elif isinstance(l_val, int) or isinstance(l_val, float):
			from sit_utils import SitUtils
			l_val = SitUtils.format_number_human_readable(l_val, 2)
		if a_with_description:
			l_tmp = '({}/{}) '.format(self.register_index, self.slave_address)
			l_tmp += self.description
			l_desc = '     {:<55}'.format(l_tmp)
		else:
			l_desc = ''
		l_res += an_item_prefix + '{:<23}'.format(self.short_description) + '{:<5}'.format('=') + '{:<25}'.format(l_val) + '{:<10}'.format(self.value_unit) + l_desc

		return l_res

# TEST FUNCTION

	def test(self):
		"""
			Test function
		"""
		try:
			print ("################# BEGIN #################")
			self._logger.info("--> ************* device models *************: %s" % (l_d.models))	 #Lists properties to be loaded with l_d.<property>.read() and then access them
			self._logger.info("-->inverter ************* l_d.inverter.points *************: %s" % (l_d.inverter.points))	#Gives the inverter available properties
			self._logger.info("-->inverter ************* common *************: %s" % (l_d.common))	
			self._logger.info("-->inverter ************* common Serial Number *************: %s" % (l_d.common.SN))	
		except Exception as l_e:
			self._logger.exception("Exception occured: %s" % (l_e))
			print('Error: %s' % (l_e))
			self._logger.error('Error: %s' % (l_e))
			sys.exit(1)


# INVARIANTS

	def invariants(self):
		assert self.valid_access_mode(self._access_mode), 'invalid access mode:{}'.format(self._access_mode)
		assert self.valid_register_index(self._register_index), 'invalid register index:{}'.format(self._register_index)

"""
Main method
"""
def main():
	#logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, filemode="a+", format="%(asctime)-15s %(levelname)-8s %(message)s")
	logger = logging.getLogger(__name__)

	try:
		l_obj = SitModbusRegister()
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
