"""
version 8 of main function with triggering and servo included included

NOW WITH START OF A HELPER FUNCTION

Overview of main function (31/3/2026 CK and BR)

this main has an updated file system:
-all housekeeping data is saved to one file
-all raised errors saved to an error log
-trigger check information is saved to a trigger log
-thermal sensor frames saved to two seperate logs:
    - background frames saved to data_log
    - frames taken immediately after trigger (in the quick burst of sensor captures) saved to post_trigger_data_log
    

Loop actions sequence:
1. take housekeeping data
2. check for trigger conditions, then activate servo and take quick burst of frames if triggered
3. check for timing for transmissions. If timing is right for science or telemetry packages, send them
    - what is sent will depend on wether the valve has triggered and there are post-trigger frames to send or not

"""

import gc
from ms5611 import MS5611
from ds18b20 import DS18B20
from mlx90640 import MLX90640, RefreshRate
from gps_v2 import SQTGPS
from triple_t import Comms
from triggering_v2 import SQTtrigger
from servo_2 import Servo

from helper import Helper

#import sdcard
#import sdcard_v2 as sdcard        # using second version of sdcard class from adafruit forums
import uos as os
import time
import machine
import array
import struct
import math
import random

from machine import Pin, SPI

#SETUP: USING HELPER FUNCTIONS TO INITIALIZE THE SD CARD, SENSORS, AND OTHER FUNCTIONS WE NEED
helper = Helper()
sd, vfs = helper.init_sd_card()  # sd card
file_list = helper.make_files()  # making files
pressure_sensor, temp_sensor, frame_taker, gps_sensor, TTT, servo_motor = helper.init_sensors(file_list)   # init sensors
triggering = SQTtrigger()   # init triggering class

# FLAG SETUP: setting all the flags and counters

trigger = False       # flag to trigger valve
trigger_condition = None      # to set trigger condition too so we know what message to send
counter = 1     # for timing transmitions
error_counter = 0
science_frame_count = 0
science_data = []
science_times = []
current_gps_data = [time.time(), 'None', 'None', 'None', 99.99]

p_list = []     # lists of pressure and altitude saved on pico for trigger check. Deleated when triggered to save space
a_list = []

# THE MAIN LOOP:

while True:

    # 1. pressure sensor
    
    if pressure_sensor:
        time.sleep_ms(100)
        try:
            pressure_T, pressure_P = pressure_sensor.log_pressure()

        except Exception as e:
            t = time.time()
            helper.log_error(t, e, "Pressure Sensor", file_list[2])

    #2. temperature sensors (internal and external)
            
    if temp_sensor:
        time.sleep_ms(100)
        try:
            #temp_sensor.log_temp(file_list[0])
            tempE, tempI = temp_sensor.read_temp(file_list[2])  # recently swaped tempE and tempI cuz I think I had them backwards

        except Exception as e:
            t = time.time()
            #writing error to error log
            helper.log_error(t, e, "Temperature Sensor", file_list[2])

    #3. GPS
    if gps_sensor:
        time.sleep_ms(100)
        try:
            gps_data = gps_sensor.gps_log()

        except Exception as e:
            t = time.time()
            helper.log_error(t, e, "GPS Sensor", file_list[2])
 
    #4. Making a list of housekeeping data:
    house_list = helper.make_house_list(pressure_T, pressure_P, tempE, tempI, gps_data, file_list) 
    p_list, a_list = helper.update_a_p_lists(house_list, p_list, a_list)  #list for triggering, capped at the latest 12 values each
    
    if gps_data[1]:
        current_gps_data = gps_data   #s etting current_gps_data to the latest good string (or the baseline Nones)

    
    #5. TRIGGER CHECK (only happends when trigger = False).
    
    if not trigger:
        
        try:      # trying to run trigger check
            #if counter == 5:
            #    trigger, condition, pres, alt = triggering.trigger_check(30, house_list[8], a_list, p_list, file_list[2])
            #else:
                
            trigger, condition, pres, alt = triggering.trigger_check(p_list[-1], a_list[-1], a_list, p_list, file_list[2])
            t = time.time()
            #print(p_list[-1], a_list[-1])
            #print(f"TRIGGER FROM CHECK: {trigger}, {condition}, {pres}, {alt}")
            
            try:            # just in case the SD card dies, put in try/except
                with open(file_list[3], "a") as f:
                    f.write(f"{t}, {trigger}, {condition}, {pres}, {alt} \n")
            except: pass
        
        except:  # keeps trigger and condition false in case of errors (may not be needed)
            trigger = False
            condition = None
            pres = house_list[2]
            alt = house_list[8]
        
        # testing seting a trigger for memory and servo activation:
        #if counter > 50:
        #    trigger = True
        
        if trigger: #and counter > 50:
            
            # 1. change thermal sensor freq to handle quicker refresh rate
            frame_taker = helper.reinit_frame_taker(file_list, before = True)

            #2. run servo
            try:
                servo_motor.run_servo()
            except Exception as e:
                t = time.time()                
                helper.log_error(t, e, "Servo Activation", file_list[2])
            
            #3. get science frames:
            
            for i in range(16):
                # getting 16 science frames in a row right after the servo triggers
                try:
                    science_frame = helper.init_float_array(768)
                    frame_taker.get_frame(science_frame)
                except Exception as e:
                    #writing error to error log
                    t = time.time()
                    helper.log_error(t, e, "MLX Science Acqui.", file_list[2])
     
                
                t = time.time()
                
                science_times.append(t)
                science_data.append(science_frame)
                
            try:
                print(science_frame)
                
                with open(file_list[4], "a") as f:
                    for i, line in enumerate(science_data):
                        f.write(f"Time: {science_times[i]} \n")
                        for temp in line:
                            f.write(f"{temp},")
                        f.write("\n")

            except:
                print("DID NOT WRITE TO POST TRIGGER DATA")
            
            
            #4. change this i2c bus frequency back to what the pressure sensor and slower frame rate needs:
            frame_taker = helper.reinit_frame_taker(file_list, before = False)


    #6. Thermal Sensor
    for _ in range(2): #take two pics to fill out checkerboard
        try:
            if frame_taker:
                frame = helper.init_float_array(768)
                frame_taker.get_frame(frame)
                t = time.time()

                try:
                    with open(file_list[1], "a") as f:
                        f.write(f"{t} FRAME DATA: \n")
                        for temp in frame:
                            f.write(f"{temp},")
                        f.write("\n")
                except: pass
            
        except Exception as e:
            try:
                with open(file_list[2], "a") as file:
                    file.write(f"{time.time()}, {e}, Thermal Sensor \n")
            except: pass

        time.sleep_ms(100)       
            


    #7. Data downlinks: check counter for timing of science and telem packet sending
    
    print(f"FREE MEMORY: {gc.mem_free()}")
    
    if TTT:
        if counter == 1 or counter % 8 == 0: 
            print("Sending science packet")
            
            if not trigger:
                TTT.science_packet(trigger, condition, pres, alt, frame)
                
                del(frame)    # delete frame from pico memoery after sending
                
            elif trigger and counter > 50:
                
                try:
                    science_frame = science_data[science_frame_count % len(science_data)]
                    TTT.science_packet(trigger, condition, pres, alt, science_frame)
                except Exception as e:
                    try:
                        with open(file_list[2], "a") as file:
                            file.write(f"{time.time()}, {e}, Thermal Sensor \n")
                    except: pass
                        
                
                
        if counter == 2 or counter % 6 == 0:
            print("Sending telemetry packet")

            error_counter = TTT.telem_packet(house_list, error_counter)
            
            print(f"what EC is set to: {error_counter}")

        
    print(f'########LOOP COUNTER {counter} ###################')
    counter += 1
    
    if trigger:
        science_frame_count += 1
    time.sleep(1)
