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
#       @creation: 20200407
#       @last modification:
#       @version: 1.0
#       @URL: $URL
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# INCLUDES
try:
	import sys
	import os.path
#	import os, errno
	import logging # http://www.onlamp.com/pub/a/python/2005/06/02/logging.html
	from logging import handlers
#	import argparse
#	from datetime import datetime, date, time, timedelta
##	import jsonpickle # pip install jsonpickle
##	import json
except ImportError as l_err:
	print("ImportError: {0}".format(l_err))
	raise l_err

class SitLogger(object):

# CONSTANTS
	DEFAULT_LOGGING_LEVEL = logging.DEBUG #For console overrided by --verbose
	DEFAULT_FILE_LOGGING_LEVEL = logging.DEBUG #For file
	DEFAULT_LOG_DIRECTORY = '/var/log/solarity' #without ending slash
	#DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
	DEFAULT_FORMAT = "%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s"

# VARIABLES
	__logger = None
	__log_directory = DEFAULT_LOG_DIRECTORY


# FUNCTIONS DEFINITION 

	def __init__(self):
		"""
			Initialize
		"""
		try:
			if not os.path.isdir(self.__log_directory):
				l_msg = 'log file path not found, check if it has been created -%s-' % self.__log_directory
				print(l_msg)
				exit(1)
			#*** Logger
			#self.__logger = self.new_logger(__name__)
		except OSError as l_e:
			self.__logger.warning("init-> OSError, probably rollingfileAppender" % (l_e))
			if e.errno != errno.ENOENT:
				raise
		except Exception as l_e:
			print('Error in init: %s' % (l_e))
			#exit(1)

	def formatter(self):
		l_res = logging.Formatter(self.DEFAULT_FORMAT)
		return l_res

	def new_logger(self, a_name, a_mac=None):
		try:
			l_res = logging.getLogger(a_name) 
			if not len(l_res.handlers): #avoid multiple handlers with same instance https://stackoverflow.com/a/31800084/2118777
				l_res.propagate = False
				l_res.setLevel(logging.DEBUG)

				l_file_handler = handlers.RotatingFileHandler(self.logger_file_name_with_host_mac(a_name, a_mac), maxBytes=5242880, backupCount=10)
				l_file_handler.setFormatter(self.formatter())
				l_file_handler.setLevel(self.DEFAULT_FILE_LOGGING_LEVEL)

				l_res.addHandler(l_file_handler)
				self.add_console_handler(l_res)

			return l_res
		except OSError as l_e:
			self.__logger.warning("new_logger-> OSError, probably rollingfileAppender" % (l_e))
			if e.errno != errno.ENOENT:
				raise l_e
		except Exception as l_e:
			raise l_e

	def add_console_handler(self, a_logger):
		l_console_handler = logging.StreamHandler(sys.stdout)
		l_console_handler.setFormatter(self.formatter())
		l_console_handler.setLevel(self.DEFAULT_LOGGING_LEVEL)
		a_logger.addHandler(l_console_handler)

	def logger_file_name_with_host_mac(self, a_name, a_mac=None):
		l_mac = a_mac
		if l_mac is None:
			l_mac = 'no_mac'

		l_res = "{0}/{1}_{2}.log".format(self.DEFAULT_LOG_DIRECTORY, a_name, l_mac)

		return l_res

	def test(self):
		"""
			Test function
		"""
		try:
			print ("################# BEGIN #################")
			self.__logger.info("--> ************* device models *************: %s" % (l_d.models))	 #Lists properties to be loaded with l_d.<property>.read() and then access them
			self.__logger.info("-->inverter ************* l_d.inverter.points *************: %s" % (l_d.inverter.points))	#Gives the inverter available properties
			self.__logger.info("-->inverter ************* common *************: %s" % (l_d.common))	
			self.__logger.info("-->inverter ************* common Serial Number *************: %s" % (l_d.common.SN))	
		except Exception as l_e:
			self.__logger.exception("Exception occured: %s" % (l_e))
			print('Error: %s' % (l_e))
			self.__logger.error('Error: %s' % (l_e))
			sys.exit(1)


def main():
	"""
	Main method
	"""
	#logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, filemode="a+", format="%(asctime)-15s %(levelname)-8s %(message)s")
	logger = logging.getLogger(__name__)

	try:
		l_obj = SitLogger()
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
