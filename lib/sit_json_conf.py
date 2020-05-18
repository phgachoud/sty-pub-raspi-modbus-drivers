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
#       @creation: 20200408
#       @last modification:
#       @version: 1.0
#       @URL: $URL
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# INCLUDES
try:
	import sys
	import os.path
	sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))
	import os, errno
	import logging # http://www.onlamp.com/pub/a/python/2005/06/02/logging.html
	from logging import handlers
	import argparse
	#sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pysunspec'))
	from datetime import datetime, date, time, timedelta
#	import jsonpickle # pip install jsonpickle
	import json
	from sit_logger import SitLogger
	from sit_constants import SitConstants
	#from sit_date_time import SitDateTime
except ImportError as l_err:
	print("ImportError: {0}".format(l_err))
	raise l_err

class SitJsonConf(object):

# CONSTANTS

# VARIABLES
	_logger = None
	_config_dir = None #Setted by init
	_config_file = None #File name only
	_config_data = None # Where json.dump are put

# FUNCTIONS DEFINITION 

	def __init__(self, a_config_file_name=SitConstants.SIT_JSON_DEFAULT_CONFIG_FILE_NAME):
		"""
			Initialize
		"""
		self._config_dir = SitConstants.DEFAULT_CONF_DIR
		self._config_file = a_config_file_name
		if not os.path.isdir(self._config_dir):
			raise Exception('init->Config dir {} does not exist, sudo mkdir -m 777 {}'.format(self._config_dir, self._config_dir))	
		try:
			self._logger = SitLogger().new_logger(__name__)
			if __name__ == '__main__':
				self.init_arg_parse()
			self.read_config(self.configuration_file_path())
		except OSError as l_e:
			self._logger.warning("init-> OSError, probably rollingfileAppender:{}".format(l_e))
			if l_e.errno != errno.ENOENT:
				raise l_e
		except Exception as l_e:
			self._logger.error('Error in init: {}'.format(l_e))
			raise l_e

	def configuration_file_path(self):
		"""
		"""
		l_res = os.path.join(self._config_dir, self._config_file)
		return l_res

	def read_config(self, a_config_file_path=None):
		"""
			puts into self._config_data json data
		"""
		if a_config_file_path is None:
			l_config_file_path = self.configuration_file_path()
		else:
			l_config_file_path = a_config_file_path
		with open(l_config_file_path, "r") as l_file:
			self._config_data = json.load(l_file)

	def item(self, a_key):
		"""
		returns value of given key exception if not found
		"""
		l_res = None
		return l_res


# SCRIPT ARGUMENTS

	def init_arg_parse(self):
		"""
			Parsing arguments
		"""
		self._logger.debug('init_arg_parse-> begin')
		self._parser = argparse.ArgumentParser(description='Actions with sunspec through TCP')
		self._add_arguments()
		l_args = self._parser.parse_args()
		self._args = l_args

	def _add_arguments(self):
		"""
		Add arguments to parser (called by init_arg_parse())
		"""
		self._parser.add_argument('-v', '--verbose', help='increase output verbosity', action="store_true")
		self._parser.add_argument('-u', '--update_leds_status', help='Updates led status according to spec', action="store_true")
		self._parser.add_argument('-t', '--test', help='Runs test method', action="store_true")

		#self._parser.add_argument('-u', '--base_url', help='NOT_IMPLEMENTED:Gives the base URL for requests actions', nargs='?', default=self.DEFAULT_BASE_URL)
		l_required_named = self._parser.add_argument_group('required named arguments')
#		l_required_named.add_argument('-i', '--host_ip', help='Host IP', nargs='?', required=True)
#		l_required_named.add_argument('-u', '--slave_address', help='Slave address of modbus device', nargs='?', required=True)
		l_required_named.add_argument('-m', '--host_mac', help='Host MAC', nargs='?', required=True)
#		l_required_named.add_argument('-l', '--longitude', help='Longitude coordinate (beware timezone is set to Chile)', nargs='?', required=True)
#		l_required_named.add_argument('-a', '--lattitude', help='Lattitude coordinate (beware timezone is set to Chile)', nargs='?', required=True)
#		l_required_named.add_argument('-d', '--device_type', help='Device Type:' + ('|'.join(str(l) for l in self.DEVICE_TYPES_ARRAY)), nargs='?', required=True)

	def execute_corresponding_args( self ):
		"""
			Parsing arguments and calling corresponding functions
		"""
		if self._args.verbose:
			self._logger.setLevel(logging.DEBUG)
		else:
			self._logger.setLevel(logging.INFO)
		if self._args.test:
			self.test()
		#if self._args.store_values:

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
		l_obj = SitJsonConf()
		l_obj.execute_corresponding_args()
#		l_id.test()
	except KeyboardInterrupt:
		logger.exception("Keyboard interruption")
	except Exception as l_e:
		logger.exception("Exception occured:{}".format(l_e))
		raise l_e


#Call main if this script is executed
if __name__ == '__main__':
    main()
