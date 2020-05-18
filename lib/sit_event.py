#!/usr/bin/env python3
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#       DESCRIPTION: 
#
#       CALL SAMPLE:
#	
#	REQUIRE
#
#       CALL PARAMETERS:
#               1) 
#
#       @author: Philippe Gachoud
#       @creation: 20191214
#       @last modification:
#       @version: 1.0
#       @URL: $URL
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
	#from sit_constants import SitConstants
	#from sit_date_time import SitDateTime
except ImportError as l_err:
	print("ImportError: {}".format(l_err))
	raise l_err

class SitEvent(object):

# CONSTANTS


# VARIABLES
	_logger = None
	_method_to_call = None

# SETTERS AND GETTERS

	@property
	def method_to_call(self):
		return self._logger

	@method_to_call.setter
	def logger(self, v):
		self._method_to_call = v


# INITIALIZATION 

	def __init__(self, a_method_to_call):
		"""
			Initialize
		"""
		try:
			self._logger = SitLogger().new_logger(__name__)
			self._method_to_call = a_method_to_call
		except OSError as l_e:
			self._logger.warning("init-> OSError, probably rollingfileAppender:{}".format(l_e))
			if e.errno != errno.ENOENT:
				raise l_e
		except Exception as l_e:
			self._logger.error('Error in init: {}'.format(l_e))
			raise l_e
			#exit(1)

# EVENTS CALL

	def call_method_to_call(self, some_positional_args, some_keyword_args):
		"""
		https://stackoverflow.com/a/706735/2118777
		"""
		assert self._method_to_call is not None, 'setted _method_to_call'
		if some_positional_args is None:
			self._method_to_call()
		elif some_keyword_args is None:
			self._method_to_call(*some_positional_args)
		else:
			self._method_to_call(*some_positional_args, **some_keyword_args)

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
#		l_obj = Template()
#		l_obj.execute_corresponding_args()
#		l_id.test()
	except KeyboardInterrupt:
		logger.exception("Keyboard interruption")
	except Exception as l_e:
		logger.exception("Exception occured:{}".format(l_e))
		raise l_e


#Call main if this script is executed
if __name__ == '__main__':
    main()
