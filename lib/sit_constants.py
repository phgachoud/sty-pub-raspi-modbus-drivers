#!/usr/bin/env python
# encoding: utf-8
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#
#       DESCRIPTION: Constants
#
#
#		*************************************************************************************************
#       @author: Philippe Gachoud
#       @creation: 20200408
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


class SitConstants(object):

	DEFAULT_CONF_DIR = '/etc/opt/solarity'
	SIT_JSON_DEFAULT_CONFIG_FILE_NAME = 'sit_general_config.json'

	DOWNLOAD_SPEED_MIN=1.5 #Mb/s                                                                                                                                                                                                                                           
	UPLOAD_SPEED_MIN=1.1 #Mb/s
	DOWNLOAD_SPEED_GOOD=3.0 #Mb/s
	UPLOAD_SPEED_GOOD=2.0 #Mb/s


	DEVICE_TYPE_SMA_INVERTER_MANAGER = 'sma_inverter_manager'
	DEVICE_TYPE_SMA_CLUSTER_CONTROLLER = 'sma_cluster_controller'
	DEVICE_TYPE_SMA_DATA_MANAGER = 'sma_data_manager'


	DEFAULT_HELP_LICENSE_NOTICE = """Solarity modbus library 
									\n Copyright (C) 2019 Philippe Gachoud (ph.gachoud@gmail.com)
									\n This library comes with ABSOLUTELY NO WARRANTY; for details
									\n type '--help'.  This is free software under LGPL_v2 LICENSE, 
									\n and you are welcome to redistribute it under certain conditions; 
									\n type '--help' for details."""
