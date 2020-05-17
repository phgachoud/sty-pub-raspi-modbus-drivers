# Summary of project
Solarity is an enterprise involved in Photovoltaic systems. The IT department works on various projects basically to get informations from PV associated devices, show its status and do required jobs to maintain the plants. The technologies used are mostly debian linux, eiffel, python, postgresql and angular.

# dependencies (as tested on a raspberry pi 3B+ with raspbian 9 and 10, linux commands are put here for reference and quick installation)
	
## included as submodules to this project
		git@github.com:sunspec/pysunspec.git
		git@github.com:jebeaudet/SunriseSunsetCalculator.git


	`sudo apt-get install python-pygments python-pip python-pymodbus python3-pip python3-serial
	sudo pip3 install serial requests click pymodbus prompt_toolkit`

# Tips and tricks:

In case pip3 install fails `sudo pip3 install --upgrade setuptools` helped me
	
