#!/usr/bin/env python3
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#       DESCRIPTION: Register events to be generated, see child classes
#

#		*************************************************************************************************
#       @author: Philippe Gachoud
#       @creation: 20191214
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
	import logging # http://www.onlamp.com/pub/a/python/2005/06/02/logging.html
	from logging import handlers
	import argparse
	#sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pysunspec'))
	from datetime import datetime, date, time, timedelta
#	import jsonpickle # pip install jsonpickle
#	import json
	from sit_logger import SitLogger
	from sit_event import SitEvent
	#from sit_modbus_register import SitModbusRegister
	#from sit_constants import SitConstants
	#from sit_date_time import SitDateTime
except ImportError as l_err:
	print("ImportError: {0}".format(l_err))
	raise l_err

class SitModbusRegisterEvent(SitEvent):

# CONSTANTS


# VARIABLES
	_logger = None
	_modbus_register = None

# SETTERS AND GETTERS

	@property
	def modbus_register(self):
		return self._modbus_register()

	@modbus_register.setter
	def modbus_register(self, v):
		self._modbus_register = v

# INITIALIZE

	def __init__(self, a_method_to_call):
		"""
			Initialize
		"""
		super().__init__(a_method_to_call)
		try:
			#*** Logger
			self._logger = SitLogger().new_logger(__name__)
		except OSError as l_e:
			self._logger.warning("init-> OSError, probably rollingfileAppender:{}".format(l_e))
			if e.errno != errno.ENOENT:
				raise l_e
		except Exception as l_e:
			self._logger.error('Error in init: {}'.format(l_e))
			raise l_e
			#exit(1)

# EVENT CALL

	def call_method_to_call(self, some_positional_args, some_keyword_args):
		"""
		Redefine
		"""
		assert self._modbus_register is not None, 'setted _modbus_register'
		super().call_method_to_call(some_positional_args, some_keyword_args)

# TEST

	def test(self):
		"""
			Test function
		"""
		try:
			self._logger.info("################# BEGIN #################")
			self._logger.info("--> ************* device models *************: {}".format(l_d.models))	 #Lists properties to be loaded with l_d.<property>.read() and then access them
		except Exception as l_e:
			self._logger.exception("Exception occured:  {}".format(l_e))
			print('Error: {}'.format(l_e))
			self._logger.error('Error: {}'.format(l_e))
			sys.exit(1)

#################### END CLASS ######################

def main():
	"""
	Main method
	"""
	#logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, filemode="a+", format="%(asctime)-15s %(levelname)-8s %(message)s")
	logger = logging.getLogger(__name__)

	try:
		pass
		#l_obj = SitModbusRegister(None)
#		l_id.test()
	except KeyboardInterrupt:
		logger.exception("Keyboard interruption")
	except Exception as l_e:
		logger.exception("Exception occured:{}".format(l_e))
		raise l_e


#Call main if this script is executed
if __name__ == '__main__':
    main()
