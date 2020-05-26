#!/usr/bin/env python
# encoding: utf-8
"""
Constants.py
"""

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
