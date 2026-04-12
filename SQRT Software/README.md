## Current SQRT Software

This file contains all the SQRT mission software. 
Code is updated as of 11/4/2026. 

## Directory

1. **main.py**: the main function that runs automatically when the onboard computer (Raspberry Pi Pico 2) is connected to power
2. **sensors/ :** this folder contains scripts with classes used to interface with the sensors onboard (GPS, ms5611 pressure sensor,
     ds18b20 temp sensors, MLX90640 thermal sensor)
3. **operations/ :** this folder contains scripts with both classes used to interface with non-sensor components (TTT and related classes, sd card, servo motor)
     and classes used for software operations (triggering algorithm, helper class functions).

## Description of Scripts:

1. main.py: the main function
2. ds18b20.py: contains ds18b20 class used to interface with ds18b20 sensors and return collected data.
3. ms5611.py: contains ms5611 class used to interface with ms5611 pressure sensor to collect, calibrate, and store data.
4. gps_v2.py: contains SQTGPS class used to interface with GPS module and listen for GGA NMEA sentences, decode them, and return required position and time data.
5. mlx90640.py: contains class used to interface with Adafruit MLX90640 thermal sensor to collect, calibrate, and return arrays of spatial temperature data.
6. sdcard_v2.py: contains class used to interface with sd card.
7. helper.py: contains class used to initialize sensors, handle data in Pico memory, create sd card files, apend data (science, housekeeping, error logs) to sd card files.
8. triggering_v2.py: contains the triggering algorithm class used to check for the conditions for triggering the experiment
9. 
