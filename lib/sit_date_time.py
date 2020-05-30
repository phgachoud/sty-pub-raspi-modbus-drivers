#!/usr/bin/env python3
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#       DESCRIPTION: 
#			Date and times functions
#
##		*************************************************************************************************
##       @author: Philippe Gachoud
##       @creation: 20200408
##       @last modification:
##       @version: 1.0
##       @URL: $URL
##		*************************************************************************************************
##		Copyright (C) 2020 Solarity spa
##
##		This library is free software; you can redistribute it and/or
##		modify it under the terms of the GNU Lesser General Public
##		License as published by the Free Software Foundation; either
##		version 2.1 of the License, or (at your option) any later version.
##
##		This library is distributed in the hope that it will be useful,
##		but WITHOUT ANY WARRANTY; without even the implied warranty of
##		MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
##		Lesser General Public License for more details.
##
##		You should have received a copy of the GNU Lesser General Public
##		License along with this library; if not, write to the Free Software
##		Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
##		*************************************************************************************************
##
##@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

# INCLUDES
try:
	import sys
	import os.path
	sys.path.append(os.path.join(os.path.dirname(__file__), './third_party/SunriseSunsetCalculator/'))
#	import os, errno
#	import logging # http://www.onlamp.com/pub/a/python/2005/06/02/logging.html
#	from logging import handlers
#	import argparse
	#sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pysunspec'))
	from datetime import datetime, date, time, timedelta
	from sunrise_sunset import SunriseSunset
	from sit_logger import SitLogger
#	import jsonpickle # pip install jsonpickle
#	import json
	from sit_json_conf import SitJsonConf
	from sit_utils import SitUtils
except ImportError as l_err:
	print("ImportError: {0}".format(l_err))
	raise l_err

#filename: my_class.py
class SitDateTime(object):

# CONSTANTS

	DAY, NIGHT = 1, 2

# VARIABLES

	_logger = None

# SETTERS AND GETTERS

# FUNCTIONS DEFINITION 

	def __init__(self):
		self._logger = SitLogger().new_logger(__name__)

	def localOffsetHours(self):
		"""
		returns local offset in hours
		ex. Chile -3 or -4
		"""
		l_res = 0
		l_cmd = 'date +%z'
		try:
			l_code, l_stdout, l_stderr = SitUtils.system_call(l_cmd)
		except Exception as l_e:
			self._logger.error ('localOffsetHours error'.format (l_e))
			raise l_e
		assert l_res <= -3
		self._logger.debug('localOffsetHours-> cmd_res:{} res:{}'.format(l_stdout, l_res))
		l_res = int(l_cmd)

		return l_res
		
		return l_res

	def time_is_between(self, a_time_to_check, an_on_time, an_off_time):
		"""
			https://stackoverflow.com/a/20518510/2118777

			l_on_time = datetime.time(23,30)
			l_off_time = datetime.time(4,15)
			l_timenow = datetime.datetime.now().time()
			l_current_time = datetime.datetime.now().time()

			l_is_day, l_matching = check_time(l_current_time, l_on_time, l_off_time)
			if l_matching:
				if l_is_day == NIGHT:
					print('Night Time detected.')
				elif l_is_day == DAY:
					print('Day Time detected.')
		"""
		if an_on_time > an_off_time:
			if a_time_to_check > an_on_time or a_time_to_check < an_off_time:
				return self.NIGHT, True
		elif an_on_time < an_off_time:
			if a_time_to_check > an_on_time and a_time_to_check < an_off_time:
				return self.DAY, True
		elif a_time_to_check == an_on_time:
			return None, True
		return None, False

	def time_is_into_sunrise_sunset(self, a_date_time, a_longitude, a_latitude, a_local_offset=-3, a_sunrise_interval_min=0, a_sunset_interval_min=0):
		"""
			is given a_date_time into sunrise sunset range?
			return boolean
		"""
		l_ss = SunriseSunset(datetime.now(), latitude=a_latitude,
			longitude=a_longitude, localOffset=a_local_offset)
		l_sunrise_time, l_sunset_time = l_ss.calculate()
		l_res = (l_sunrise_time + timedelta(seconds=a_sunrise_interval_min * 60) < datetime.now() and 
			l_sunset_time - timedelta(seconds=a_sunset_interval_min * 60) > datetime.now())
		self._logger.debug('time_is_into_sunrise_sunset-> sunrise_time:{} sunset_time:{} datetime:{} result (sun is up?):{}'.format(l_sunrise_time, l_sunset_time, a_date_time, l_result))

		return l_res


	def now_is_into_sunrise_sunset_from_conf(self, a_sit_json_conf):
		"""
		"""
		assert isinstance(a_sit_json_conf, SitJsonConf)

		l_longitude = self._sit_json_conf.item('longitude')
		l_latitude = self._sit_json_conf.item('latitude')
		l_local_offset = self._sit_json_conf.item('local_offset')
		l_sunrise_interval_minutes = self._sit_json_conf.item('sunrise_interval_minutes')
		l_sunset_interval_minutes = self._sit_json_conf.item('l_sunset_interval_minutes')
		l_res = time_is_into_sunrise_sunset(datetime.now(), l_longitude, l_latitude, l_local_offset, l_sunrise_interval_minutes, l_sunset_interval_minutes)

		return l_res

def main():
	"""
	Main method
	"""
	#logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, filemode="a+", format="%(asctime)-15s %(levelname)-8s %(message)s")



if __name__ == '__main__':
    main()
