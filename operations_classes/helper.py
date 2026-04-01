"""
helper.py

class for helpful functions that will help us

"""

import os
import machine
import time
import array
import random
import struct

class Helper:
    
    def __init__(self):
        print("initializing the helper class")
        
        
        
    def log_error(self, t, exception, location, error_log):
        """Function to log an error in the error_log
        Inputs: time (float?), exception (string), location (string), path to error log (string)
        Output: writes to error log
        """
        
        try:
            with open(error_log, "a") as file:
                file.write(f"{t}, {exception}, {location} \n")
        except: pass
        
        
    def make_files(self, error_log):
        """Function to make all the files on the sd card and give them headers"""
        
        #constants for pin numbers n things
        SPI_BUS = 1
        SCK_PIN = 10
        MOSI_PIN = 11
        MISO_PIN = 12
        CS_PIN = 13
        SD_MOUNT_PATH = '/sd'
        
        n = str(random.randint(1, 10000))
        
        # our list of file names
        file_list = [
            '/sd/housekeeping_log' + n  + '.csv',
            '/sd/data_log' + n + '.csv',
            '/sd/error_log' +n + '.csv',
            '/sd/trigger_log' + n + '.csv',
            '/sd/post_trigger_data_log' + n + '.csv'     # to specifically hold frames taken imediately after trigger for ease of transmitting them 
        ]
        
        try:

            # Small delay before file ops
            time.sleep_ms(50)

            # Initialize log files
            for fname in file_list:
                with open(fname, 'w') as f:
                    if 'house' in fname:
                        f.write("Timestamp, ms5611 Temperature (C), Pressure (mbar), TempE (deg), TempI (deg), Lat (deg), Lon (deg), Alt (m), HDOP \n")
                    elif 'data_log' in fname:
                        f.write("MLX90640 Raw Data Values \n")
                    elif 'trigger' in fname:
                        f.write("Timestamp, Trigger, Condition, Pressure (mbar), Alt (m) \n")
                    else:
                        f.write("Timestamp, Error, Cause \n")           # recording of errors by time and what cause

            print(f" Files created at time {time.time()}")
        
        except Exception as e:
            self.log_error(time.time(), e, "File Logging")
        
        
        
