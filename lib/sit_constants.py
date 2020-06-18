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

	# Sunspec registers short abbreviations see sunspec into wiki links to github repo to find them

#	SS_REG_SHORT_ABB_ = "" #
	SS_REG_SHORT_ABB_MANUFACTURER = "Mn" # Manufacturer
	SS_REG_SHORT_ABB_MODEL = "Md" # Model
	SS_REG_SHORT_ABB_OPTIONS = "Opt" # Options
	SS_REG_SHORT_ABB_VERSION = "Vr" # Version
	SS_REG_SHORT_ABB_SERIAL_NUMBER = "SN" # Serial number
	SS_REG_SHORT_ABB_MODBUS_DEVICE_ADDRESS = "DA" # Modbus device address
	SS_REG_SHORT_ABB_PARITY_EVEN = "Pad" # Parity even forced
	#INVERTER
	SS_REG_SHORT_ABB_AC_CURRENT = "A" # AC Current
	SS_REG_SHORT_ABB_AC_PHASE_A = "AphA" # Amps Phase A
	SS_REG_SHORT_ABB_AC_PHASE_B = "AphB" # Amps Phase B
	SS_REG_SHORT_ABB_AC_PHASE_C = "AphC" # Amps Phase C
	SS_REG_SHORT_ABB_V_PP_AB = "PPVphAB" # Phase to phase Voltage AB
	SS_REG_SHORT_ABB_V_PP_BC = "PPVphBC" # Phase to phase Voltage BC
	SS_REG_SHORT_ABB_V_PP_CA = "PPVphCA" # Phase to phase Voltage CA
	SS_REG_SHORT_ABB_V_PN_A = "PhVphA" # Phase Voltage AN
	SS_REG_SHORT_ABB_V_PN_B = "PhVphB" # Phase Voltage BN
	SS_REG_SHORT_ABB_V_PN_C = "PhVphC" # Phase Voltage CN
	SS_REG_SHORT_ABB_AC_POWER = "W" # AC Power Watts Active power in Watts
	SS_REG_SHORT_ABB_HZ = "Hz" # Line Frequency
	SS_REG_SHORT_ABB_AC_Q_APPARENT_POWER = "VA" # Apparent Power
	SS_REG_SHORT_ABB_AC_S_REACTIVE_POWER = "VAr" # Reactive Power
	SS_REG_SHORT_ABB_DC_AMPS = "DCA" # DC Current in Amps
	SS_REG_SHORT_ABB_DC_VOLTAGE = "DCV" # DC Voltage
	SS_REG_SHORT_ABB_DC_POWER = "DCW" # DC Power in Watts
	SS_REG_SHORT_ABB_TEMP_CAB = "TmpCab" # Cabinet Temperature
	SS_REG_SHORT_ABB_STATUS_OPERATING_STATE = "St" #

#	SS_REG_SHORT_ABB_ = "" #
#	SS_REG_SHORT_ABB_ = "" #



	SS_REG_SHORT_EXTRA_HUAWEI_PLANT_STATUS = 'PlantSt' # Plant Status 1 unlimited power / 2 limited power 3 = ildle / 4 = Outage fault, maintenance /5 = communication interrupt
	SS_REG_SHORT_EXTRA_HUAWEI_ACT_POWER_ADJ = 'ActPAdj' # Active Adjustment
	SS_REG_SHORT_EXTRA_HUAWEI_ACT_POWER_ADJ_PCT = 'ActPAdjPct' # Active Adjustment percentage



