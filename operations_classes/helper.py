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
        
        
    def make_files(self):
        """Function to make all the files on the sd card and give them headers"""
        
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
            
            return file_list
            
        except Exception as e:
            print(f"cant make files: {e}")
            
            
    def make_house_list(pT, pP, tI, tE, gps_data, file_list):
        """Function to make our housekeeping data list,
        and should handle any issues with if we did not collect good data in the last
        
        Will also try to save housekeeping data to the sd card
        """
        
        # making the housekeeping data list:
        
        if not pT:
            pT = 'None'
        if not pP:
            pP = 'None'
        if not tI:
            tI = 'None'
        if not tE:
            tE = 'None'
        if not gps_data:
                gps_data = current_gps_data
        elif len(gps_data) != 5:                 # in case some value is missing
            diff = 5 - len(gps_data)
            
            for i in diff:
                gps_data.append(99.99)
        
        t = time.time()
            
        house_list = [t, pressure_T, pressure_P, tempE, tempI, gps_data[1], gps_data[2], gps_data[3], gps_data[4]]
        
        # tring to save the housekeeping data as a line in the hosuekeeping sd card:
        
        try:
            with open(file_list[0], "a") as file:
                file.write(f"{t}, {pT}, {pP}, {tE}, {tI}, {gps_data[1]}, {gps_data[2]}, {gps_data[3]}, {gps_data[4]} \n") 
        except Exception as e:
            self.log_error(t, e, "Making House List", file_list[2])
        
        return house_list
    
    def update_a_p_lists(house_list, p_list, a_list):
        """Function to append values ot a list,
        and cap the list at the latest 12 values
        Done for both alt and 
        Inputs: house list (from housekeeping values), lists of p values and a values
        Output: updated val_list (list)
        """
            p_list.append(house_list[2])
            a_list.append(house_list[8])
            
            
            if len(p_list) > 12:
                p_list.pop(0)
            
            if len(a_list) > 12:
                a_list.pop(0)
            
        return p_list, a_list 
        
   
