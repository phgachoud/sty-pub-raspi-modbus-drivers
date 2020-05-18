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
	sys.path.append(os.path.join(os.path.dirname(__file__), '../lib'))
	import os, errno
	import subprocess
	import logging # http://www.onlamp.com/pub/a/python/2005/06/02/logging.html
	from logging import handlers
	import argparse
	from collections import OrderedDict
	#sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pysunspec'))
	from datetime import datetime, date, time, timedelta
#	import jsonpickle # pip install jsonpickle
#	import json
	from sit_modbus_register import SitModbusRegister
	from sit_logger import SitLogger
	#from sit_constants import SitConstants
	#from sit_date_time import SitDateTime
except ImportError as l_err:
	print("ImportError: {0}".format(l_err))
	raise l_err

class SitUtils(object):

# CONSTANTS


# VARIABLES
	_logger = None

# SETTERS AND GETTERS

	@property
	def logger(self):
		return self._logger

	@logger.setter
	def logger(self, v):
		self._logger = v

# INITIALIZE

	def __init__(self):
		"""
			Initialize
		"""
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

# ARGUMENTS

	@staticmethod
	def args_to_list(some_args_as_string, a_target_type='int'):
		"""
		some_args_as_string as either 1-10 | 1,2,3 | 3
		"""
		assert some_args_as_string is not None, 'some_args_as_string not None'
		l_res = []
		if '-' in some_args_as_string:
			l_tmp = some_args_as_string.split('-')
			l_first = int(l_tmp[0])
			l_last = int(l_tmp[1])
			#print('args_to_list-> l_tmp:{} first:{} last:{}'.format(l_tmp, l_first, l_last))
			for l_i in range(l_first, l_last + 1):
				l_res.append(l_i)
				#print('args_to_list-> l_i:{} first:{} last:{}'.format(l_i, l_first, l_last))
		elif ',' in some_args_as_string:
			l_tmp = some_args_as_string.split(',')
			for l_i in l_tmp:
				l_res.append(int(l_i))
		elif len(some_args_as_string) > 0:
			try:
				l_res.append(int(some_args_as_string))
			except Exception as l_e:
				raise Exception('args_to_list->Unable to parse args data as int:{}'.format(some_args_as_string))
		else:
			raise Exception('args_to_list->Unable to parse args data:{}'.format(some_args_as_string))

		assert isinstance(l_res, list), 'l_res is not a list'
		#print('args_to_list-> l_res:{}'.format(l_res))
		return l_res

# COLLECTIONS

	@staticmethod
	def od_extend(an_ordered_dict, a_sit_modbus_register):
		assert isinstance(an_ordered_dict, OrderedDict), 'an_ordered_dict is an OrderedDict'
		assert isinstance(a_sit_modbus_register, SitModbusRegister), 'a_sit_modbus_register is an SitModbusRegister but {}'.format(a_sit_modbus_register.__class__.__name__)

		an_ordered_dict[a_sit_modbus_register.short_description] = a_sit_modbus_register


# SYSTEM

	@staticmethod
	def send_mail(a_dest_list, a_subject, a_body_list, an_attach_list=None):
		"""
		Sends with mail command as system command
		"""
		assert len(a_dest_list) > 0, 'destinatory not empty'
		assert not '"' in a_subject, 'No " into subject'

		if an_attach_list is not None and len(an_attach_list) > 0:
			l_attachments = ''
			for l_attach in an_attach_list:
				l_attachments += ' -A ' + l_attach
		else:
			l_attachments = None

		l_dests = ''
		for l_dest in a_dest_list:
			l_dests += l_dest + ', '
		if l_dest.endswith(', '):
			l_dest = l_dest[:-2]
		assert not l_dest.endswith(', ')

		#MULTILINE
#		l_body_echos = ''
#		for l_body_elt in a_body_list:
#			l_line = "echo '{}'".format(l_body_elt) + "\n"
#			l_line = l_line.decode('ascii')
#			l_body_echos += l_line

		#ONE LINE ONLY
		#l_cmd = '{{ {} }}|mail -s "{}" '.format(l_body_echos, a_subject)
		assert not '"' in a_body_list[0], 'No " into string'
		l_body_echos = 'echo "' + a_body_list[0] + '"'

		l_cmd = ' {} |mail -s "{}" '.format(l_body_echos, a_subject)
		if l_attachments is not None:
			l_cmd += l_attachments
		l_cmd += ' ' + l_dests

		l_return_code, l_stdout, l_stderr = SitUtils.system_call(l_cmd)

		if l_return_code != 0:
#			l_return_code = subprocess.call(l_cmd + l_email_to, shell=True)  
			l_msg = 'send_email-> Could not send email, return_code:{},\n\tl_stdout:{} \n\tl_cmd=-{}-'.format(l_return_code, l_stderr, l_cmd)
			raise Exception(l_msg) #Otherwise file is never created

	@staticmethod
	def system_call(a_cmd):
		"""
			Returns return_code, stdout, stderr
		"""
		l_proc = subprocess.Popen(a_cmd,
			shell=True,
			stdout = subprocess.PIPE,
			stderr = subprocess.PIPE,
		)
		stdout, stderr = l_proc.communicate()
	 
		return l_proc.returncode, stdout, stderr	

# FORMATTING

	@staticmethod
	def format_number_human_readable(a_val, a_float_digits_count=2):
		"""
		"""
		assert isinstance(a_val, int) or isinstance(a_val, float), 'a_val is int or float, no its an {}'.format(a_val.__class__.__name__)
		if isinstance(a_val, int) or isinstance(a_val, float):
			if isinstance(a_val, float):
				l_fmt = '{:,.' + str(a_float_digits_count) + 'f}'
			else:
				l_fmt = '{:,}'
			l_res = l_fmt.format(a_val)
			l_res = l_res.replace(',', '\'')
		else:
			raise Exception('not implemented')
		#print('********************a_val:{}- l_res:{}- l_type:{}'.format(a_val, l_res, a_val.__class__.__name__))
		return l_res

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
		l_obj = SitUtils()
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
