CURRENTLY NOT TESTED WAIT FOR SOME DAYS TO BE READY

# Summary of project
Solarity is an enterprise involved in Photovoltaic systems. The IT department works on various projects basically to get informations from PV associated devices, show its status and do required jobs to maintain the plants. The technologies used are mostly debian linux, eiffel, python, postgresql and angular.

As responsible for IT department I'd like to share the maximum of code I can so that I contribute to this big concept of knowledge sharing through humanity.

I recommend for ethical purpose to **[use sourceforge repository](https://sourceforge.net/projects/sty-pub-raspi-modbus-drivers/)** more than [github](https://github.com/phgachoud/sty-pub-raspi-modbus-drivers) since github belongs to microsoft I personnaly don't agree with many ethical choices.

Sorry for inconsistencies and things that need some more time to be as good as I would like to be.

# Documentation
  * Into this file
  * Into the doc directory the manuals
  * Into each file a peace of documentation
  * Ask and I'll be happy to answer you and complete the missing ones.

# Generalities
  * For each driver the --help option will give you some informations
  * Each file will generate a csv when the option --store_values is invoqued
    * CSV file format are with metadata starting with #, column abbreviations, lines of data
    * stored into /var/solarity/yyyy/mm (feel free to add an option for that directory ;))
    * filenames are yyyymmdd_ipAddress_macAddress_slaveAddress_driverName.py.csv
  * Timestamps are in UTC
  * Coma separated

# Requirements 
as tested on a raspberry pi 3B+ with raspbian 9 and 10, linux commands are put here for reference and quick installation
	
## included as submodules to this project
		git@github.com:sunspec/pysunspec.git
		git@github.com:jebeaudet/SunriseSunsetCalculator.git


	`sudo apt-get install python-pygments python-pip python-pymodbus python3-pip python3-serial
	sudo pip3 install serial requests click pymodbus prompt_toolkit`

# Installation

  * Nothing more than this repository with libs, above requirements and run the code mentioned into file header

# License

This project is under [LGPLv2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html), see LICENCE file

# Tips and tricks:

In case pip3 install fails `sudo pip3 install --upgrade setuptools` helped me
	

# Devices and drivers
You'll find samples into the sample directory
## SUNSPEC
Tested on ABB device PVS 100 and TRIO 50, documentation into doc/ABB directory and example into sunspec_device.py file, also working on SMA inverter_manager
## SMA
### Inverter manager, inverters and janitza (energy meter) attached to it
respectivly
  * /sma/inverter_manager.py
  * /sma/sunny_tripower_60.py 
  * /sma/janitza_UMG604.py
### Cluster controller and inverters (sma energy meter) attached to it
respectivly
  * /sma/cluster_controller.py
  * /sma/cluster_controller_inverter.py
## Schneider PM 5500 series (tested on 5560)
  * /sma/schneider_pm5500.py

## Legrand comunication module 145671 which is for meter model 14668
  * /sma/legrand_145671.py


