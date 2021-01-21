#!/usr/bin/env python3
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#       DESCRIPTION: 
#			Library for mobdbus operations, see cluster_controller.py for example of use
#
#	REQUIRE
#		**** PYTHON *****
#		sudo apt-get install python-pygments python-pip python-pymodbus python3-pip
#		sudo pip install -U pymodbus click requests prompt_toolkit 
#
#		**** PYTHON 3 *****
#		sudo apt install python3-pip
#		sudo pip3 install requests click pymodbus prompt_toolkit
#
#		*************************************************************************************************
#       @author: Philippe Gachoud
#       @creation: 20200402
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
#
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# INCLUDES
try:
	import sys
	import os.path
	import os, errno
	sys.path.append(os.path.join(os.path.dirname(__file__), '../lib')) #the way to import directories
	import logging # http://www.onlamp.com/pub/a/python/2005/06/02/logging.html
	from logging import handlers
	import csv
	import socket
	import pymodbus
	import serial
	from pymodbus.pdu import ModbusRequest
	from pymodbus.client.sync import ModbusSerialClient #initialize a serial RTU client instance https://github.com/riptideio/pymodbus/blob/master/pymodbus/client/sync.py
	from pymodbus.client.sync import ModbusTcpClient # FOR TCP
	from pymodbus.transaction import ModbusRtuFramer
	from pymodbus.exceptions import ModbusException, ConnectionException
	import time
	import requests
	import argparse
	from datetime import datetime
	import struct
	import json  #for pretty printing in log

	from pymodbus.constants import Endian
	from pymodbus.payload import BinaryPayloadBuilder
	from pymodbus.payload import BinaryPayloadDecoder
	from collections import OrderedDict

	from sit_logger import SitLogger
	from sit_modbus_register import SitModbusRegister
	from sit_json_conf import SitJsonConf
	from sit_constants import SitConstants

	#sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) + '/DLSS/dlss_libs/')
except ImportError as l_err:
	print("ImportError: {0}".format(l_err))
	raise l_err

class SitModbusDevice (object):

# CONSTANTS
	DEFAULT_LOGGING_LEVEL=logging.DEBUG #For console overrided by --verbose
	DEFAULT_FILE_LOGGING_LEVEL=logging.DEBUG #For file
	DEFAULT_BASE_URL="http://localhost:9999/" # with ending slash
	DEFAULT_PORT="/dev/ttyUSB0" #https://unix.stackexchange.com/a/144735/47775 to get it
	TARGET_MODE_TCP = 'tcp'
	TARGET_MODE_RTU = 'rtu'
	DEFAULT_TARGET_MODE = TARGET_MODE_TCP # or rtu
	DEFAULT_TARGET_PORT = 502
	MAX_CONNECT_RETRIES_COUNT = 3
	MAX_MODBUS_REGISTER_RETRIES_COUNT = 3

	LOG_FILE_PATH = '/var/log/solarity'
	DEFAULT_CSV_FILE_LOCATION = '/var/solarity' #without ending slash
	PARSER_DESCRIPTION = 'Actions with modbus device. ' + SitConstants.DEFAULT_HELP_LICENSE_NOTICE

# VARIABLES
	_logger = None
	_args = None
	_console_handler = None
	_file_handler = None

	_sit_json_conf = None

	_modbus_client = None
	_is_connected = False
	_base_url = DEFAULT_BASE_URL

	_target_ip = None
	_target_port = DEFAULT_TARGET_PORT
	_target_mode = DEFAULT_TARGET_MODE
	_slave_address = None 
	_client_connect_retries = 3
	_rtu_timeout = 1 #seconds
	_rtu_stopbits = 1
	_rtu_bytesize = 8
	_rtu_parity = 'E'
	_rtu_baudrate =  19200 #9600
	_byte_order = Endian.Big
	_word_order = Endian.Big
	_substract_one_to_register_index = False



	_sit_modbus_registers = OrderedDict() # OrderedDict

# FUNCTIONS DEFINITION 

	def __init__(self, a_slave_address, a_target_mode=DEFAULT_TARGET_MODE, a_port=DEFAULT_PORT, an_ip_address=None):
		"""
		Initialize
		@param a_slave_address
		@param a_target_mode
		@param a_port
		@param an_ip_address
		"""
		assert self.valid_slave_address(a_slave_address), 'invalid a_slave_address:{}'.format(a_slave_address)

		self._target_port = a_port
		self._slave_address = a_slave_address
		self._target_ip = an_ip_address

		self._logger = SitLogger().new_logger(self.__class__.__name__)
		self._sit_json_conf = SitJsonConf(__name__)
		self._target_mode = a_target_mode

		if self._target_mode == self.TARGET_MODE_TCP:
			assert self.valid_ip(self._target_ip), 'valid ip address'
		self.invariants()


	def process_script_arguments(self):
		"""
		reads script arguments and executes corresponding argument
		"""
		try:
			self.init_arg_parse()
			self.connect()
			self.execute_corresponding_args()
		except Exception as l_e:
			self._logger.exception('process_script_arguments->Exception:%s' % (l_e))
			if self.is_connected():
				self.disconnect()

	def connect(self):
		"""
		sets self._modbus_client and connects to it
		"""
		if self._target_mode == self.TARGET_MODE_TCP:
			assert self.valid_ip(self._target_ip), 'Target ip is None'
		assert not self.is_connected()

		l_retries_count = 0
		self._logger.debug('connect-> with args target_mode:{} port:{} rtu_timeout:{} baudrate:{}'.format(self._target_mode, self._target_port, self._rtu_timeout, self._rtu_baudrate))
		while l_retries_count < self.MAX_CONNECT_RETRIES_COUNT and not self._is_connected:
			try:
				if self._target_mode == self.TARGET_MODE_RTU:
					assert os.geteuid() == 0, 'user must be root for RTU mode'
					# DOC: https://github.com/riptideio/pymodbus/blob/8ef32997ee1da1cd465f2e19ff3b54b93d38728c/pymodbus/repl/main.py
					self._modbus_client = ModbusSerialClient(method=self._target_mode, port=str(self._target_port), timeout=self._rtu_timeout, stopbits=self._rtu_stopbits, bytesize=self._rtu_bytesize, parity=self._rtu_parity, baudrate=self._rtu_baudrate)
					self._modbus_client.debug_enabled = True
					self._logger.debug('connect->target:{} port:{} timeout:{} stopbit:{} bytesize:{} parity:{} baudrate:{}'.format(self._target_mode, str(self._target_port), self._rtu_timeout, self._rtu_stopbits, self._rtu_bytesize, self._rtu_parity, self._rtu_baudrate))
					self._logger.info('connect->RTU Client Mode:{}'.format(self._target_mode))
				else:
					assert self._target_mode == self.TARGET_MODE_TCP
					self._modbus_client = ModbusTcpClient(self._target_ip, port=str(self._target_port), retries=self._client_connect_retries, retry_on_empty=True)
					self._logger.info('connect->TCP Client Mode:{}'.format(self._target_mode))

				#Connect to the serial modbus server
				connection = self._modbus_client.connect()
				if self._modbus_client.connect:
					#self._logger.debug("Client is connected")
					self._is_connected = True
					self._logger.info('connect -> Connection success')
				else:
					self._is_connected = False
					raise ConnectionException("connect->Could not connect to _modbus_client")
			except ConnectionException as l_e:
				l_retries_count += 1
				self._logger.exception("connect->ConnectionException occured during connection, retrying:{}".format(l_e))
				time.sleep(1)
			except Exception as l_e:
				self._logger.exception("connect->Exception occured during connection:{}".format(l_e))
				raise l_e

# HIGH LEVEL FUNCTIONS

	def _header_rows (self):
		#return [['#Mn', 'some_manufacturer'], ['#Md', 'some_model']]
		return []

	def add_modbus_register_from_values(self, a_short_description, a_description, a_register_index, a_register_type, a_slave_address, an_access_mode=SitModbusRegister.ACCESS_MODE_R, a_value_unit=None, a_scale_factor_register_index=None, an_event=None, an_is_metadata=False):
		""" 
		adds to self._sit_modbus_registers
		"""
		assert not a_short_description in self._sit_modbus_registers.keys(), 'Already has key ' + a_short_description
		self._sit_modbus_registers[a_short_description] = SitModbusRegister(a_short_description, a_description, a_register_index, a_register_type, an_access_mode, a_value_unit, a_scale_factor_register_index=a_scale_factor_register_index, an_event=an_event, an_is_metadata=an_is_metadata)

	def add_modbus_register(self, a_modbus_register):
		assert isinstance(a_modbus_register, SitModbusRegister), 'arg is not a SitModbusRegister but {}'.format(a_modbus_register.__class__.__name__)
		assert a_modbus_register.has_slave_address(), 'a_modbus_register has no slave_address'
		self._sit_modbus_registers[a_modbus_register.short_description] = a_modbus_register

	def append_modbus_registers(self, an_ordered_dict):
		"""
		add_modbus_register with each item of given an_ordered_dict
		"""
		assert isinstance(an_ordered_dict, OrderedDict), 'param is not an OrderedDict'
		for l_short_desc, l_reg in an_ordered_dict.items():
			self.add_modbus_register(l_reg)

	def read_register_from_short_description(self, a_short_description, a_slave_address):
		"""
		returns a read register
		@param: a_short_description
		"""
		l_reg = self._sit_modbus_registers[a_short_description]
		self.read_sit_modbus_register(l_reg, a_slave_address)

	def read_sit_modbus_register(self, a_sit_modbus_register):
		"""
		setting value of given modbus register
		@a_sit_modbus_register
		"""
		assert isinstance(a_sit_modbus_register, SitModbusRegister), 'given argument must be a SitModbusRegister'
		assert self.is_connected(), 'Not connected'

		l_val = self.register_value(a_sit_modbus_register.register_index, a_sit_modbus_register.words_count, a_sit_modbus_register.slave_address)

		a_sit_modbus_register.set_value_with_raw(l_val)

		self.set_value_with_scale_factor(a_sit_modbus_register)

	def set_value_with_scale_factor(self, a_sit_modbus_register):
		"""
		set a_sit_modbus_register value with read scale_factor read from scale_factor_register_index
		"""
		if a_sit_modbus_register.scale_factor_register_index is not None:
			l_scale_factor = self.register_values_int_16_s(a_sit_modbus_register.scale_factor_register_index, a_sit_modbus_register.slave_address)
			l_val = a_sit_modbus_register.value
			l_val = l_val * 10 ** l_scale_factor
			self._logger.debug('set_value_with_scale_factor-> old_val:%s scale_factor:%s new_val:%s' % (a_sit_modbus_register.value, l_scale_factor, l_val))
			a_sit_modbus_register.value = l_val
#		else:
#			self._logger.debug('read_sit_modbus_register-> scale_factor_index should be None:%s' % (a_sit_modbus_register.scale_factor_register_index))

	def read_all_sit_modbus_registers(self):
		"""
			Reads all registers and print result as debug
		"""
		self._logger.debug('read_all_sit_modbus_registers-> registers to read count({}) start --------------------------------------------------'.format(len(self._sit_modbus_registers)))

		for l_short_desc, l_sit_reg in self._sit_modbus_registers.items():
			self.read_sit_modbus_register(l_sit_reg)
			if l_sit_reg.has_post_set_value_call():
				l_sit_reg.call_post_set_value()
			#self._logger.debug('read_all_registers-> sit_register.out():%s' % (l_sit_reg.out()))
			self._logger.debug('read_all_registers-> sit_register.out_short():%s' % (l_sit_reg.out_short()))


# LOW LEVEL FUNCTIONS READ

	def register_value(self, a_register_index, a_register_length, a_slave_address):
		"""
		Returns a given register value
		@a_register_length: 1 register is 16 bits (2 bytes = 1 word)
		"""
		assert self.is_connected(), 'register_value->device is not connected'
		assert isinstance(a_register_index, int), 'register_value->Slave address is not an int'
		assert self.valid_slave_address(a_slave_address), 'register_value->Slave address is not valid:' + str(a_slave_address)

		#self._logger.debug('register_value-> _substract_one_to_register_index:%s' % (self._substract_one_to_register_index))
		if self._substract_one_to_register_index:
			l_register_index = a_register_index - 1
			l_register_index_s_debug = str(a_register_index) + '-1'
		else:
			l_register_index = a_register_index
			l_register_index_s_debug = str(l_register_index)
		l_retries_count = 0
		while l_retries_count < self.MAX_MODBUS_REGISTER_RETRIES_COUNT:
			try:
				#Starting add, num of reg to read, slave unit.
				self._logger.debug('register_value-> index:{} length:{} unit:{} _substract_one_to_register_index:{}'.format(l_register_index, a_register_length, a_slave_address, self._substract_one_to_register_index))
				l_result = self._modbus_client.read_holding_registers(l_register_index, a_register_length, unit=a_slave_address) # Average current
				if l_result is not None:
					if (hasattr(l_result, 'function_code') and 
							l_result.function_code < 0xFFFFFFFF):
						self._logger.debug("register_value-> read register index:%s (%s) length:%s slave_address:%s" % (l_register_index, l_register_index_s_debug, a_register_length, a_slave_address))
						#self._logger.debug(l_result)
						#self._logger.debug("register_value->register 0 value:%s" % l_result.getRegister(1))
						#self._logger.debug("register_value-> 0 type:%s" % type(l_result.getRegister(0)))
						#self._logger.debug(l_result._str_())
					else:
						self._logger.error("register_value-> returned code is invalid: {}".format(l_result))
				else:
					l_msg = "register_value-> No register received, l_result is None"
					self._logger.error(l_msg)
					raise ModbusException(l_msg)

				if not hasattr(l_result, 'registers'):
					l_msg = 'register_value-> read register has no registers attribute, slave:{} reading register:{} length:{}'.format(a_slave_address, l_register_index, a_register_length)
					self._logger.error(l_msg)
					raise ModbusException(l_msg)

				return l_result
			except KeyboardInterrupt:
				self._logger.exception("register_value-> Keyboard interruption")
			except ModbusException as l_e:
				l_retries_count += 1
				if l_retries_count >= self.MAX_MODBUS_REGISTER_RETRIES_COUNT:
					self._logger.error('register_value-> error with ModbusException not retrying but raising')
					raise l_e
				else:
					self._logger.error('register_value-> error with ModbusException retrying {}'.format(l_retries_count))
					self.disconnect
					time.sleep(0.2)
					self.connect
			except Exception as l_e:
				self._logger.exception("register_value-> Exception occured, msg:%s" % l_e)
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
		self._logger.debug("************************************* _int_from_register-> register(%s) binary (%s) %s:%s => %s result(%s)" % (a_register, l_tmp_binary, l_start_index, l_end_index, l_tmp, l_result))
		return l_result

		
	def register_values_date_time(self, a_register_index, a_slave_address):
		"""
		from spec returns a string formated 
		@a_register_index: a register index
		"""
		assert False, 'Deprecated'
		try:
			l_register_res = self.register_value_invalid_int(a_register_index, 4, a_slave_address)
			self._logger.debug("******* BEGIN ****************************** register_values_date_time->a_register_index:%s" % (a_register_index))
			l_year = self._int_from_register(l_register_res.registers[0], 0, 6) + 2000
			l_day = self._int_from_register(l_register_res.registers[1], 0, 4)
			l_month = self._int_from_register(l_register_res.registers[1], 8, 4)
			l_min = self._int_from_register(l_register_res.registers[2], 0, 5)
			l_hour = self._int_from_register(l_register_res.registers[2], 8, 5)
			l_sec = int(int(l_register_res.registers[3]) / 1000)


			l_result = str(l_year) + '-' + str(l_month).zfill(2) + '-' + str(l_day).zfill(2) + 'T' + str(l_hour).zfill(2) + ':' + str(l_min).zfill(2) + ':' + str(l_sec).zfill(2) + 'Z' #Definitive result as expecte
		except Exception as l_e:
			self._logger.exception("register_values_date_time exception: %s" % l_e)
			raise l_e

		l_result = (';'.join(str(l) for l in l_register_res.registers)) # only decimals
		self._logger.debug("******** END ***************************** register_values_date_time->registers:%s- result:%s-" % (l_register_res.registers, l_result))
		return l_result

	def register_values_pm5500_date_time(self, a_register_index, a_slave_address):
		"""
		from spec returns a string formated with datetime
		@a_register_index: a register index start index, the followings will be read
		"""
		l_i = 0
		l_register_res = self.register_value_invalid_int(a_register_index + l_i, 1, a_slave_address)
		l_year = l_register_res.registers[0]
		l_i = l_i + 1
		l_register_res = self.register_value_invalid_int(a_register_index + l_i, 1, a_slave_address)
		l_month = l_register_res.registers[0]
		l_i = l_i + 1
		l_register_res = self.register_value_invalid_int(a_register_index + l_i, 1, a_slave_address)
		l_day = l_register_res.registers[0]
		l_i = l_i + 1
		l_register_res = self.register_value_invalid_int(a_register_index + l_i, 1, a_slave_address)
		l_hour = l_register_res.registers[0]
		l_i = l_i + 1
		l_register_res = self.register_value_invalid_int(a_register_index + l_i, 1, a_slave_address)
		l_min = l_register_res.registers[0]
		l_i = l_i + 1
		l_register_res = self.register_value_invalid_int(a_register_index + l_i, 1, a_slave_address)
		l_sec = l_register_res.registers[0]
		l_i = l_i + 1

		l_result = str(l_year) + str(l_month).zfill(2) + str(l_day).zfill(2) + 'T' + str(l_hour).zfill(2) + str(l_min).zfill(2) + str(l_sec).zfill(2) + 'Z'

		self._logger.debug("register_values_pm5500_date_time->result:%s" % l_result)
		return l_result
		
	def register_values_float_32(self, a_register_index, _slave_address):
		"""
		from spec returns a float from given register index
		@a_register_index: a register index
		"""
		l_register_res = self.register_value_invalid_int(a_register_index, 2, a_slave_address)
		#self._logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=self._byte_order, wordorder=self._word_order) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		#https://pymodbus.readthedocs.io/en/v1.3.2/library/payload.html?highlight=binarypayloaddecoder#pymodbus.payload.BinaryPayloadDecoder
		l_result = decoder.decode_32bit_float()
		if not instance(l_result, float):
			self._logger.error("register_values_float_32-> result of decode_32bit_float is not a float but:'%s'" % l_result)
			l_result = 0
		self._logger.debug("register_values_float_32->after decoder:%s" % l_result)
		return l_result

	def register_values_float_32_pf(self, a_register_index, _slave_address):
		"""
		from spec returns a float from given register index for power factor
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
		l_register_res = self.register_value(a_register_index, 2, a_slave_address)
		#self._logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		#https://pymodbus.readthedocs.io/en/v1.3.2/library/payload.html?highlight=binarypayloaddecoder#pymodbus.payload.BinaryPayloadDecoder
		l_result = decoder.decode_32bit_float()
		if l_result > 1:
			l_result = 2 - l_result
		elif l_result < -1: 
			l_result = -2 - l_result
		else:
			pass
		self._logger.debug("register_values_float_32_pf->after decoder:%s" % l_result)
		return l_result

	def register_values_string_8(self, a_register_index, _slave_address):
		"""
		from spec returns a string
		@a_register_index: a register index
		"""
		l_register_res = self.register_value(a_register_index, 8, a_slave_address)
		#self._logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		#https://pymodbus.readthedocs.io/en/v1.3.2/library/payload.html?highlight=binarypayloaddecoder#pymodbus.payload.BinaryPayloadDecoder
		l_result = decoder.decode_string(8)
		if len (l_result) > 0 and str(l_result[0]) == '0':
			l_result = ''
		else:
			l_result = l_result.decode('utf-8', errors='replace')
		#self._logger.debug("register_values_string16->after decoder:%s" % l_result)

		assert isinstance(l_result, str), 'result is no str but' + l_result.__class.__name__
		return l_result

	def register_values_string_16(self, a_register_index, a_slave_address):
		"""
		from spec returns a word from given register index
		@a_register_index: a register index
		"""
		l_register_res = self.register_value(a_register_index, 16, a_slave_address)
		#self._logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		#https://pymodbus.readthedocs.io/en/v1.3.2/library/payload.html?highlight=binarypayloaddecoder#pymodbus.payload.BinaryPayloadDecoder
		l_result = decoder.decode_string(16)
		if len (l_result) > 0 and str(l_result[0]) == '0':
			l_result = ''
		else:
			l_result = l_result.decode('utf-8', errors='replace')
		#self._logger.debug("register_values_string16->after decoder:%s" % l_result)

		assert isinstance(l_result, str), 'result is no str but' + l_result.__class.__name__
		return l_result

	def register_values_int_16_s(self, a_register_index, a_slave_address):
		"""
		from spec returns a word from given register index
		@a_register_index: a register index
		"""
		l_register_res = self.register_value(a_register_index, 1, a_slave_address)
		#self._logger.debug("register_values_16_s->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		#https://pymodbus.readthedocs.io/en/v1.3.2/library/payload.html?highlight=binarypayloaddecoder#pymodbus.payload.BinaryPayloadDecoder
		l_result = decoder.decode_16bit_int()
		#self._logger.debug("register_values_u_word->after decoder:%s" % l_result)
		assert isinstance(l_result, int), 'result is no int but' + l_result.__class.__name__
		return l_result

	def register_values_int_16_u(self, a_register_index, a_slave_address):
		"""
		from spec returns an int
		@a_register_index: a register index
		"""
		l_register_res = self.register_value(a_register_index, 1, a_slave_address)
		#self._logger.debug("register_values_int_16_u->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		#https://pymodbus.readthedocs.io/en/v1.3.2/library/payload.html?highlight=binarypayloaddecoder#pymodbus.payload.BinaryPayloadDecoder
		l_result = decoder.decode_16bit_uint()
		#self._logger.debug("register_values_int16_u->after decoder:%s" % l_result)
		return l_result

	def register_values_int_32_u(self, a_register_index, a_slave_address):
		"""
		from spec returns a long from given register index
		@a_register_index: a register index
		"""
		l_register_res = self.register_value(a_register_index, 2, a_slave_address)
		#self._logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		#https://pymodbus.readthedocs.io/en/v1.3.2/library/payload.html?highlight=binarypayloaddecoder#pymodbus.payload.BinaryPayloadDecoder
		l_result = decoder.decode_32bit_uint()
		#self._logger.debug("register_values_int_32_u->after decoder:%s" % l_result)
		return l_result

	def register_values_int_32_s(self, a_register_index, a_slave_address):
		"""
		from spec returns a long from given register index
		@a_register_index: a register index
		"""
		l_register_res = self.register_value(a_register_index, 2, a_slave_address)
		#self._logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		#https://pymodbus.readthedocs.io/en/v1.3.2/library/payload.html?highlight=binarypayloaddecoder#pymodbus.payload.BinaryPayloadDecoder
		l_result = decoder.decode_32bit_int()
		#self._logger.debug("register_values_int_32_u->after decoder:%s" % l_result)
		return l_result

	def register_values_int_64_u(self, a_register_index, a_slave_address):
		"""
		from spec returns a long from given register index
		@a_register_index: a register index
		"""
		l_register_res = self.register_value(a_register_index, 4, a_slave_address)
		#self._logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		#https://pymodbus.readthedocs.io/en/v1.3.2/library/payload.html?highlight=binarypayloaddecoder#pymodbus.payload.BinaryPayloadDecoder
		l_result = decoder.decode_64bit_uint()
		#self._logger.debug("register_values_int_32_u->after decoder:%s" % l_result)
		return l_result

	def register_values_int_64_s(self, a_register_index, a_slave_address):
		"""
		from spec returns a long from given register index
		@a_register_index: a register index
		"""
		l_register_res = self.register_value(a_register_index, 4, a_slave_address)
		#self._logger.debug("register_values_u_long->before decoder:%s" % l_register_res.registers)
		decoder = BinaryPayloadDecoder.fromRegisters(l_register_res.registers, byteorder=Endian.Big, wordorder=Endian.Big) #https://pymodbus.readthedocs.io/en/latest/source/example/modbus_payload.html
		#https://pymodbus.readthedocs.io/en/v1.3.2/library/payload.html?highlight=binarypayloaddecoder#pymodbus.payload.BinaryPayloadDecoder
		l_result = decoder.decode_64bit_int()
		#self._logger.debug("register_values_int_32_u->after decoder:%s" % l_result)
		return l_result

# FILE OUTPUT

	def store_values_into_csv(self, an_ordered_dict, a_slave_address):
		"""
		Stores values into CSV  into self.get_csv_file_path()
		@param a_row_dict: an OrderedDict
		"""
		assert isinstance(an_ordered_dict, OrderedDict), 'param is not an OrderedDict'
		assert isinstance(a_slave_address, int), 'param is not an int'
		try:
			l_f_name = self.csv_file_path(a_slave_address)
			l_file_exists = os.path.isfile(l_f_name)
			self._logger.info("store_values_into_csv->Writting into file %s exists:%s" % (l_f_name, l_file_exists))
			with open(l_f_name, mode='a+') as l_csv_file:
				l_csv_writter = csv.writer(l_csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
				for l_header_row in self._header_rows():
					self._logger.info("store_values_into_csv->writting header:{}".format(l_header_row))
					l_csv_writter.writerow(l_header_row)
				# Metadata and registers
				l_header_list = []
				l_values_dict = []
				l_values_dict.append(datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'))
				for l_reg in an_ordered_dict.values():
					if l_reg.is_metadata:
						l_header_line = []
						l_header_line.append('#' + l_reg.short_description)
						l_header_line.append(l_reg.value)
						if not l_file_exists:
							self._logger.info("store_values_into_csv->Writting METADATA row: %s" % (';'.join(str(l) for l in l_header_line)))
							l_csv_writter.writerow(l_header_line)
					else:
						l_header_list.append(l_reg.short_description)
						l_val = l_reg.value
						l_values_dict.append(l_val)
				# Header
				l_header_list.insert(0, 'Timestamp')

				assert len(l_header_list) == len(l_values_dict), 'header row {} doesnt have the same length as data row{}, hit file {}'.format(len(l_header_list), len(l_values_dict), l_f_name)

				if not l_file_exists:
					self._logger.info("store_values_into_csv->Writting HEADER row: %s" % (';'.join(str(l) for l in l_header_list)))
					l_csv_writter.writerow(l_header_list)
				#Registers no metadata
				self._logger.info("store_values_into_csv->HEADER (not written) row: %s" % ('|'.join(str(l) for l in l_header_list)))
				self._logger.info("store_values_into_csv->Writting row: %s" % ('|'.join(str(l.value) for l in an_ordered_dict.values())))
				l_csv_writter.writerow(l_values_dict)
		except Exception as l_e:
			self._logger.error('store_values_into_csv->Error: %s' % l_e)
			raise l_e

	def csv_file_path(self, a_slave_address):
		"""
		Returns the csv file path
			if test adds tests.csv at the end of file_name
		"""
		assert self._target_ip, "host ip is empty"
		assert isinstance(a_slave_address, int), "slave_address is not an int"
		assert self._args.host_mac, "host mac is empty"
#		if __debug__:
#			try:
#				socket.inet_aton(self._args.host_ip)
#			except socket.error as l_e:
#				assert False, "Host ip address is invalid"
#				raise l_e

		l_dir = self.DEFAULT_CSV_FILE_LOCATION + '/' + str(datetime.today().year) + '/' + '{:02d}'.format(datetime.today().month)
		l_result = (l_dir + '/' +
			datetime.today().strftime('%Y%m%d') + '_' + 
			self._args.host_mac.replace(':', '-') + '_' + 
			self._target_ip + '_' + 
			str(a_slave_address) + '_' + 
			os.path.basename(__file__) + '_' + self.__class__.__name__ + '.csv')
		if self._args.test:
			l_result += 'test.csv'

		try:
			os.makedirs(l_dir)
		except OSError as l_e:
			if l_e.errno == errno.EEXIST:
				pass
			else:
				self._logger.error('get_csv_file_path Error: %s' % (l_e))
				raise l_e

		return l_result

# LOW LEVEL FUNCTIONS READ

	def write_register_value(self, a_register_index, a_slave_address, a_value):
		"""
		Returns a given register value
		@a_register_index
		@a_register_length: 1 register is 16 bits (2 bytes = 1 word)
		@a_slave_address
		@a_value
		"""
		assert self.is_connected(), 'register_value->device is not connected'
		assert self.valid_slave_address(self._slave_address), 'register_value->Slave address is None'

		#self._logger.debug('register_value-> _substract_one_to_register_index:%s' % (self._substract_one_to_register_index))
		if self._substract_one_to_register_index:
			l_register_index = a_register_index - 1
			l_register_index_s_debug = str(a_register_index) + '-1'
		else:
			l_register_index = a_register_index
			l_register_index_s_debug = str(l_register_index)
		try:
			#Starting add, num of reg to read, slave unit.
			l_result = self._modbus_client.write_register(l_register_index, a_value, unit=a_slave_address) # Average current
			if l_result is not None:
				if (hasattr(l_result, 'function_code') and 
						l_result.function_code < 0xFFFFFFFF):
					self._logger.debug("register_value-> read register index:%s (%s) value:(%s) length:%s slave_address:%s" % (l_register_index, l_register_index_s_debug,'|'.join( str(l_elt) for l_elt in l_result.registers), a_register_length, self._slave_address))
					#self._logger.debug(l_result)
					#self._logger.debug("register_value->register 0 value:%s" % l_result.getRegister(1))
					#self._logger.debug("register_value-> 0 type:%s" % type(l_result.getRegister(0)))
					#self._logger.debug(l_result._str_())
				else:
					self._logger.error("register_value-> returned code is invalid: {}".format(l_result))
			else:
				self._logger.error("register_value-> No register received, l_result is None")

			if not hasattr(l_result, 'registers'):
				raise Exception('register_value-> read register has no registers attribute, reading register:' + str(l_register_index)) # TODO CORRECTME HERE

			return l_result
		except KeyboardInterrupt:
			self._logger.exception("register_value-> Keyboard interruption")
		except Exception as l_e:
			self._logger.exception("register_value-> Exception occured, msg:%s" % l_e)
			raise l_e

# CONNECTION

	def is_connected(self):
		"""
		Self explaining
		"""
		#self._logger.debug("is_connected-> %s, modbusclient:%s" % (self._is_connected, self._modbus_client))
		return self._modbus_client is not None and self._is_connected

	def disconnect(self):
		"""
		Disconnects modbus client
		"""
		assert self.is_connected()
		assert self._modbus_client is not None

		try:
			self._modbus_client.close()
			self._is_connected = False
			self._logger.info('disconnect -> Disconnection success')
		except Exception as l_e:
			self._logger.exception("disconnect->Exception occured msg:" + l_e.message)
			raise l_e

	def init_arg_parse(self):
		"""
		Parsing arguments
		override add_arg_parse if necessary
		"""
		"""App help"""
		self._parser = argparse.ArgumentParser(description=self.PARSER_DESCRIPTION)
		self.add_arg_parse()
		l_args = self._parser.parse_args()
		self._args = l_args

	def add_arg_parse(self):
		"""
		Adding arguments to parser
		"""
		# OPTIONALS
		self._parser.add_argument('-v', '--verbose', help='increase output verbosity', action="store_true")
		self._parser.add_argument('-u', '--base_url', help='NOT_IMPLEMENTED:Gives the base URL for requests actions', nargs='?', default=self.DEFAULT_BASE_URL)
		self._parser.add_argument('-s', '--store_values', help='Stores values into csv file located into ' + self.DEFAULT_CSV_FILE_LOCATION, action="store_true")
		self._parser.add_argument('-t', '--test', help='Runs test method', action="store_true")
		self._parser.add_argument('-a', '--display_all', help='Displays all register after reading them', action='store_true')
		self._parser.add_argument('-d', '--long', help='Displays all register after reading them, with long version and description', action='store_true')

		# REQUIRED
		l_required_named = self._parser.add_argument_group('required named arguments')
		l_required_named.add_argument('-i', '--host_ip', help='Host IP', nargs='?', required=True)
		l_required_named.add_argument('-m', '--host_mac', help='Host MAC', nargs='?', required=True)
		self.add_required_named(l_required_named)

	def add_required_named(self, a_required_named):
		a_required_named.add_argument('-c', '--slave_address', help='Slave address of modbus device', nargs='?', required=True)

	def execute_corresponding_args( self ):
		"""
		Calls the corresponding function to given script argument
		"""
		assert isinstance(self._slave_address, list), 'self._slave_address is list'

		if self._args.verbose:
			self._logger.setLevel(logging.DEBUG)
#			self._console_handler.setLevel(logging.DEBUG)
#			self._file_handler.setLevel(logging.DEBUG)
		else:
			self._logger.setLevel(logging.DEBUG)
#			self._console_handler.setLevel(logging.ERROR)
#			self._file_handler.setLevel(logging.DEBUG)
		if self._args.base_url:
			self._logger.debug("execute_corresponding_args->given argument was '%s'" % self._args.base_url)
			self._base_url = self._args.base_url
		if self._args.display_all or self._args.store_values or self._args.test:
			for l_slave in self._slave_address:
				assert self.valid_slave_address(l_slave), 'given slave address should be int but' + str(l_slave) 
				self.read_all_sit_modbus_registers(l_slave)
				if self._args.display_all():
					l_long = False
					if hasattr(self._args, 'long'):
						l_long = self._args.long
					print(self.out_human_readable(l_long))
				if self._args.store_values:
						self.store_values_into_csv(self._sit_modbus_registers, l_slave)
				if self._args.test:
					self.test()

# EVENTS

	def call_sit_modbus_registers_events(self):
		l_index = 0
		for l_short_desc, l_sit_reg in self._sit_modbus_registers.items():
			if l_sit_reg.has_event():
				self._logger.debug('call_sit_modbus_registers_events-> Calling event for register_short:{}'.format(l_sit_reg.out_short()))
				self._logger.debug('call_sit_modbus_registers_events-> counter:{}/{}'.format(l_index, len(self._sit_modbus_registers.items())))
				l_sit_reg.call_event()
			#self._logger.debug('read_all_registers-> sit_register.out():%s' % (l_sit_reg.out()))
			l_index += 1

# VALIDATION

	@staticmethod
	def valid_slave_address_list(a_list):
		""" List """
		assert isinstance(a_list, list), 'a_list is not a list'

		l_res = False
		if isinstance(a_list, list):
			for l_elt in a_list:
				l_res = SitModbusDevice.valid_slave_address(l_elt)
				if not l_res:
					break

		return l_res

	@staticmethod
	def valid_slave_address(an_int):
		l_res = False
		l_res = isinstance(an_int, int)
		if l_res:
			l_res = (an_int is not None) and an_int > 0 and an_int <= 253

		return l_res

	def valid_ip(self, v):
		if v is None:
			return False
		else:
			try:
				socket.inet_aton(v)
				# legal
				return True
			except socket.error:
				# Not legal
				return False


# OUTPUT

	def out_without_registers(self, a_sep='\n', an_item_prefix=''):
		l_res = ''

		l_res = l_res + an_item_prefix + 'port:' + str(self._target_port) + a_sep
		l_res = l_res + an_item_prefix + 'target_ip:' + self._target_ip + a_sep
		l_res = l_res + an_item_prefix + 'target_mode:' + self._target_mode + a_sep
		l_res = l_res + an_item_prefix + 'slave_address:' + str(self._slave_address) + a_sep
		l_res = l_res + an_item_prefix + 'client_connect_retries:' + str(self._client_connect_retries) + a_sep
		l_res = l_res + an_item_prefix + 'rtu_timeout:' + str(self._rtu_timeout) + a_sep
		l_res = l_res + an_item_prefix + 'rtu_stopbits:' + str(self._rtu_stopbits) + a_sep
		l_res = l_res + an_item_prefix + 'rtu_parity:' + self._rtu_parity + a_sep
		l_res = l_res + an_item_prefix + 'rtu_baudrate:' + str(self._rtu_baudrate) + a_sep
		l_res = l_res + an_item_prefix + 'byte_order:' + self._byte_order + a_sep
		l_res = l_res + an_item_prefix + 'word_order:' + self._word_order

		return l_res

	def out(self, a_sep='\n', an_item_prefix='\t', a_with_description=False):
		l_res = self.__class__.__name__ + a_sep
		l_res += self.out_without_registers(a_sep, an_item_prefix) + a_sep
		
		l_res += 'Registers:' + a_sep
		for l_short_desc, l_sit_reg in self._sit_modbus_registers.items():
			l_res += l_sit_reg.out_human_readable(an_item_prefix, a_with_description=a_with_description) + a_sep

		return l_res
	
	def out_human_readable(self, a_with_description=False):
		l_res = ''

		l_res += self.out('\n', '\t', a_with_description)

		return l_res

# INVARIANT

	def invariants(self):
		"""
		Raise exception if not complying
		"""
		assert self.valid_slave_address(self._slave_address), 'valid slave address'

# TEST

	def test( self ):
		"""
		Test method
		"""
		self._logger.info("Test method->")

def main():
	""" """
	logger = logging.getLogger(__name__)
	#a_slave_address, a_target_mode=DEFAULT_TARGET_MODE, a_port=DEFAULT_PORT, an_ip_address=None
	l_o = SitModbusDevice(125, SitModbusDevice.DEFAULT_TARGET_MODE, SitModbusDevice.DEFAULT_PORT, '192.168.0.1')
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
