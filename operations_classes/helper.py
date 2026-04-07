"""
helper.py

class for helpful functions that will help us

"""
import gc
from ms5611 import MS5611
from ds18b20 import DS18B20
from mlx90640 import MLX90640, RefreshRate
from gps_v2 import SQTGPS
from triple_t import Comms

from servo_2 import Servo

import sdcard_v2 as sdcard 
import os
import machine
import time
import array
import random
import struct

class Helper:
    
    def __init__(self):
        print("initializing the helper class")
        
    def init_float_array(self, size) -> array.array:
        """Function to make a float array for the thermal sensor
        Notes: This for some reason wasn't working as a function defined and used in the MLX class,
        so we're defining it here
        Input: array size
        Output: array of 0s
        """
        return array.array('f', (0 for _ in range(size)))    
        
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
            
    def init_sensors(self, file_list):
        """
        Initialises all sensors and returns
        
        Inputs:
        file_list: list of files including error log needed for exception logging.
        
        Returns:
        Bool - Proof of sensor initialisation
        """
        # Pressure Sensor
        try:
            pressure_sensor = MS5611(i2c_bus=0, sda_pin=4, scl_pin=5, address = 0x77)
        except Exception as e:
            pressure_sensor = None
            self.log_error(time.time(), e, "Pressure Sensor Init", file_list[2])

        #Temperature Sensor(s)
        try:
            temp_sensor = DS18B20(pin=21)
        except Exception as e: 
            print("Temperature Sensor Error")
            temp_sensor = None
            self.log_error(time.time(), e, "Temp Sensor(s) Init", file_list[2])

        # Thermal Sensor
        try:
            i2c = machine.I2C(
                    0,
                    scl=machine.Pin(5),
                    sda=machine.Pin(4),
                    freq=400000  
                )
            frame_taker = MLX90640(i2c, address=0x33)
            frame_taker.refresh_rate = RefreshRate.REFRESH_8_HZ                 # currently the fasted refresh rate that doesn't kill itself,
                                                                                # reason unclear and seen by many users of the product online
        except Exception as e:
            frame_taker = None
            print("MLX90640 Sensor Error")
            self.log_error(time.time(), e, "MLX Sensor Init", file_list[2])

        # GPS 
        try:
            gps_sensor = SQTGPS(uart_bus = 1, baudrate = 9600, tx_pin = 8, rx_pin = 9)
        except Exception as e:
            gps_sensor = None
            print("GPS Sensor Error")
            self.log_error(time.time(), e, "GPS Init", file_list[2])
            
        # Communications
        try:
            TTT = Comms(file_list, address = 0x53, callsign = "SQRT", uart_bus=0, tx_pin = 0, rx_pin = 1)

        except Exception as e:
            TTT = None
            print(f"T3 Error: {e}")
            self.log_error(time.time(), e, "TTT Init", file_list[2])

        #initializing servo:
        try:
            servo_motor = Servo()
        except Exception as e:
            servo_motor = None
            print("Servo initialization error")
            self.log_error(time.time(), e, "Servo Init", file_list[2])
                
        return pressure_sensor, temp_sensor, frame_taker, gps_sensor, TTT, servo_motor
    
    def reinit_frame_taker(self, file_list, before = False):
        """Function to reinitialize the thermal sensor before and after triggering,
        because we need to change the i2c clock rate for a faster burst of frames
        then change it back after so that the pressure sensor works ok
        """
        
        if before:
            try:
                frame_taker = MLX90640(i2c=0, address=0x33, sda_pin=4, scl_pin=5, freq = 1000000)
                frame_taker.refresh_rate = RefreshRate.REFRESH_8_HZ                 
                                                                                        
            except Exception as e:
                frame_taker = None
                t = time.time()
                # writing error to error log
                self.helper.log_error(t, e, "MLX Science Init", file_list[2])
        else:
            try:
                frame_taker = MLX90640(i2c=0, address=0x33, sda_pin=4, scl_pin=5, freq = 400000)
                frame_taker.refresh_rate = RefreshRate.REFRESH_8_HZ                 
                                                                                    
            except Exception as e:
                frame_taker = None
                self.helper.log_error(t, e, "MLX Science Init", file_list[2])
                
        return frame_taker
        
    
    def init_sd_card(self):
        """Function to initiate and mount the sd card
        Will also try to unmount the sd card first to solve our weird "no sd found" issue
        """
        SPI_BUS = 1
        SCK_PIN = 10
        MOSI_PIN = 11
        MISO_PIN = 12
        CS_PIN = 13
        SD_MOUNT_PATH = '/sd'
        
        try:
            # Assign chip select (CS) pin 
            cs = machine.Pin(CS_PIN, machine.Pin.OUT)

            # Intialize SPI peripheral (start with 1 MHz)
            spi = machine.SPI(SPI_BUS,
                              baudrate=500000,
                              polarity=0,
                              phase=0,
                              bits=8,
                              firstbit=machine.SPI.MSB,
                              sck=machine.Pin(SCK_PIN),
                              mosi=machine.Pin(MOSI_PIN),
                              miso=machine.Pin(MISO_PIN))
        except:
            pass
        
        # unmount if needed
        try:
            os.umount("/sd")
        except:
            pass
        
        try:

            try:
                # Initialize SD card
                sd = sdcard.SDCard(spi, cs)
            except Exception as e:
                print("sd initialise error", e)

            try:
                # Mount filesystem
                vfs = os.VfsFat(sd)
                os.mount(vfs, "/sd")
                print(f'SD card mounted at time: {time.time()}')
            except Exception as e:
                print("mount fail", e)
            
        except Exception as e:
            
            print(f"mounting error: {e}")
            pass
          
        return sd, vfs
        
    
    def make_house_list(self, pT, pP, tE, tI, gps_data, file_list):
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
            
            for _ in range(diff):
                gps_data.append(99.99)
        
        t = time.time()
            
        house_list = [t, pT, pP, tE, tI, gps_data[0], gps_data[1], gps_data[2], gps_data[3], gps_data[4]]
        
        # tring to save the housekeeping data as a line in the hosuekeeping sd card:
        
        try:
            with open(file_list[0], "a") as file:
                file.write(f"{t}, {pT}, {pP}, {tE}, {tI}, {gps_data[0]}, {gps_data[1]}, {gps_data[2]}, {gps_data[3]}, {gps_data[4]} \n") 
        except Exception as e:
            self.log_error(t, e, "Making House List", file_list[2])
        
        return house_list
    
    def update_a_p_lists(self, house_list, p_list, a_list):
        """Function to append values ot a list,
        and cap the list at the latest 12 values
        Done for both alt and 
        Inputs: house list (from housekeeping values), lists of p values and a values
        Output: updated val_list (list)
        """
        
        p_list.append(house_list[2])
        a_list.append(house_list[7])
            
            
        if len(p_list) > 12:
            p_list.pop(0)
            
        if len(a_list) > 12:
            a_list.pop(0)
            
        return p_list, a_list
    
    # Function for ensuring that a full frame is acquired rather than two frames of the same subpage (only odd pixels)
    def get_full_frame(self, frame, frame_taker):
        """
        Reads both subpages and merge into a complete 768-pixel frame.
        
        Inputs:
        frame (array) - Empty frame of size 768 created by init_float_array
        frame_taker - the initialised mlx90640 object
        
        Returns:
        Updates the frame inputted with 768 temperature values.
        """
        # Subpage booleans are initialised to check if both subpages have been used.
        subpages_read = [False, False]
        
        # the temperature frames are created.
        temp_frames = [self.init_float_array(768), self.init_float_array(768)]

        # The while loop is used to ensure that both subpages have been used.
        while not all(subpages_read):
            temp_frame = self.init_float_array(768)
            # temperatures are gotten for the 
            frame_taker.get_frame(temp_frame)  
            sub_page = frame_taker.mlx90640_frame[833]  

            temp_frames[sub_page] = temp_frame[:]
            subpages_read[sub_page] = True

        # Merging the two subpages
        for i in range(768):
            row = i // 32
            col = i % 32

        
            # Checkerboard pattern
            if (row + col) % 2 == 0:
                frame[i] = temp_frames[0][i]
            else:
                frame[i] = temp_frames[1][i]
        
    
        
        
