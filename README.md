# SQRT_Project

**SQRT Members:** Orlaith Ni Dhuill, Elyana Abdallah, Javier Ayuso, Caimin Keavney, Bruce Ritter.

**Programming language:** Python for micropython controller

**Repo Information**

This repository contains all code for the SQRT project. Older versions of code and early test data packets are included in the **old_version** branch of this repo. 

Current Use (below) will be updated to show what files are currently used on the pico. The code is structured such that a file saved as main.py on the pico can use classes for sensors and other operations as it runs on a loop. 


## File Directory
- **SQRT Software**: will conatain all final software used onboard SQRT during flight ("flight software"). Right now it just has main, and operations and sensor classes are in operations_classes and sensor_classes.
- **post-mission data analysis**: contains software used for post-mission data analysis, not run onboard.

## Current Use:  as of 6pm on8/4

Current main script: SQRT Software/main.py, with sensor and operations scrips below imported. 

Current sensor scripts (in sensor_classes): gps_v2.py, mlx90640.py, ms5611.py, ds18b20.py

Current operations scripts (in operations_classes): servo_2.py, triggering_v2.py, sdcard_v2.py, triple_t.py, tuppersat_radio.py, _packet_utils.py, rhserial.py, helper.py, gps_airborne.py

