#!/usr/bin/env python3
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#       DESCRIPTION: Register short class to define behaviour of this type of register
#
#		*************************************************************************************************
#       @author: Philippe Gachoud
#       @creation: 20200421
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
	sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
	#sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pysunspec'))
	import os, errno
	import logging # http://www.onlamp.com/pub/a/python/2005/06/02/logging.html
	from logging import handlers
	import argparse
	from pymodbus.payload import BinaryPayloadBuilder
	from pymodbus.payload import BinaryPayloadDecoder
	from sit_modbus_register import SitModbusRegister
	from pymodbus.constants import Endian
	from datetime import datetime, date, time, timedelta
	from sit_logger import SitLogger
	#from sit_constants import SitConstants
	#from sit_date_time import SitDateTime
except ImportError as l_err:
	print("ImportError: {0}".format(l_err))
	raise l_err

class RegisterTypeInt16uScaleFactor(SitModbusRegister):

# CONSTANTS


# VARIABLES
	_logger = None
	_words_count = 1
	_byte_order = Endian.Big
	_word_order = Endian.Big

	_scale_factor = None

# SETTERS AND GETTERS

	@property
	def scale_factor(self):
		return self._scale_factor

# INITIALIZATION

	def __init__(self, 
		a_short_description, 
		a_description, 
		a_register_index, 
		a_slave_address, 
		an_access_mode=SitModbusRegister.DEFAULT_ACCESS_MODE, 
		a_value_unit=None, 
		a_scale_factor_register_index=None, 
		an_event=None, 
		an_is_metadata=False, 
		a_post_set_value_call=None,
		a_scale_factor=None):
		"""
			Initialize
		"""
		try:
			#*** Logger
			self._logger = SitLogger().new_logger(__name__)
			super().__init__(
					a_short_description, 
					a_description, 
					a_register_index, 
					a_slave_address, 
					an_access_mode, 
					a_value_unit, 
					a_scale_factor_register_index, 
					an_event, 
					an_is_metadata, 
					a_post_set_value_call
				)
			self._scale_factor = a_scale_factor
			self.invariants()
		except OSError as l_e:
			self._logger.warning("init-> OSError, probably rollingfileAppender:{}".format(l_e))
			if e.errno != errno.ENOENT:
				raise l_e
		except Exception as l_e:
			self._logger.error('Error in init: {}'.format(l_e))
			raise l_e
			#exit(1)

# STATUS SETTING

	def set_value_with_raw(self, a_register_read_res):
		#self._logger.debug("set_value_with_raw->before decoder:{}".format(a_register_read_res.registers))
		decoder = BinaryPayloadDecoder.fromRegisters(a_register_read_res.registers, byteorder=self._byte_order, wordorder=self._word_order) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		#https://pymodbus.readthedocs.io/en/v1.3.2/library/payload.html?highlight=binarypayloaddecoder#pymodbus.payload.BinaryPayloadDecoder
		l_v = decoder.decode_16bit_uint()
		#self._logger.debug("set_value_with_raw->after decoder:{}".format(l_v))
		self._value = l_v


#################### END CLASS ######################

