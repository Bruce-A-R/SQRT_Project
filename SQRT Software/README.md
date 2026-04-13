# Current SQRT Software

This file contains all the SQRT mission software. 
Code is updated as of 11/4/2026. 

A directory of files and a list of file descriptions are below.  

## Directory

1. **main.py**: the main function that runs automatically when the onboard computer (Raspberry Pi Pico 2) is connected to power
2. **sensors/ :** this folder contains scripts with classes used to interface with the sensors onboard (GPS, ms5611 pressure sensor,
     ds18b20 temp sensors, MLX90640 thermal sensor)
3. **comms/ :** this folder contains classes used to interface with the TTT and downlink data. 
4. **operations/ :** this folder contains scripts with both classes used to interface with non-sensor components (sd card, servo motor)
     and classes used for software operations (triggering algorithm, helper class functions). This is all functinos not related to collecting or sending data. 

## Description of Scripts:

1. main.py: the main function
2. ds18b20.py: contains ds18b20 class used to interface with ds18b20 sensors and return collected data.
3. ms5611.py: contains ms5611 class used to interface with ms5611 pressure sensor to collect, calibrate, and store data.
4. gps_v2.py: contains SQTGPS class used to interface with GPS module and listen for GGA NMEA sentences, decode them, and return required position and time data.
5. gps_airborne.py: contains a class used to set the gps to airborne mode, provided by UCD
6. mlx90640.py: contains classes MLX90640, I2CDevice, and RefreshRate which are used to interface with Adafruit MLX90640 thermal sensor
   to collect, calibrate, and return arrays of spatial temperature data.
7. sdcard_v2.py: contains class used to interface with sd card.
8. helper.py: contains class used to initialize sensors, handle data in Pico memory, create sd card files, apend data (science, housekeeping, error logs) to sd card files.
9. triggering_v2.py: contains the triggering algorithm class used to check for the conditions for triggering experiment operations
   (Faster burst of thermal sensor data aquisition, servo activation, change in data packet transmission)
10. servo_2.py: contains Servo class used to activate the servo motor (used to open the valve for our experiment).
11. triple_t.py: contains Comms class used to interface with the TTT to transmit data.
12. _tuppersat_radio.py: contains TupperSatRadio class used to format and transmit data packets
13. _rhserial_radio.py: contains class used by Comms class and _tuppersat_radio class to transmit data packets
14. _packet_utils.py: contains TelemetryPacket, DataPacket classes
15. _utils.py: contains Counter class used by RHSerialRadio and TupperSatRadio classes
