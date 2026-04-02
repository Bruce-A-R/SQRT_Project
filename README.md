# SQRT_Project

**SQRT Members:** Orlaith Ni Dhuill, Elyana Abdallah, Javier Ayuso, Caimin Keavney, Bruce Ritter.

**Repo Information**

This repository contains all code for the SQRT project. While working on the project, each team member initially committed code to named branches so that we were not worried about overriding each other's work. This strategy eventually changed to members committing directly to the main branch after confirming an update to code with other team members. At the moment, all named branches are behind main and show a history of work before the final week(s) of software development. 

Current Use (below) will be updated to show what files are currenlty used on the pico. The code is structured such that a file saved as main.py on the pico can use classes for sensors and other operations as it runs on a loop. 


**Programming lanugage:** Python for micropython controller

**File Directory:**
- sensor_classes: contains classes written (or edited from publicly accessible code) to run sensor operations/collect data
- operations_classes: conatins classes written (or adapted) to run operations that do not collect data. helper.py, triggering_algorithm_v2.py, ect. 
- sensor_test_data: contains files and scripts used to test sensors during software development
- trigger_test_data: contains files made to bench test the triggering algorithm with simulated flight data during software development
- mains: contains main functions, including the final version used in flight


# Current Use:  as of 5pm on 2/4

Current main script: main_v8.py, with sensor and operations scrips below imported. 

Current sensor scripts: gps_v2.py, mlx90640.py, pressure_sensor.py, temperature_sensor.py

Current operations scripts: servo.py, triggering_alorithm_v2.py, sdcard_v2.py, triple_t.py, tuppersat_radio.py, _packet_utils.py, rhserial.py, helper.py
