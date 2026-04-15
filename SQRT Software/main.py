"""
main.py

Authors: Bruce Ritter, Caimin Keavney
Version Date: 14/4/2026

Test code has been removed from this main.py version. This is the final SQRT flight software main

Loop actions sequence:
1. take housekeeping data
2. check for trigger conditions, then activate servo and take quick burst of frames if triggered
3. check for timing for transmissions. If timing is right for science or telemetry packages, send them
    - what is sent will depend on wether the valve has triggered and there are post-trigger frames to send or not

"""
# imports:
import gc
from ms5611 import MS5611
from ds18b20 import DS18B20
from mlx90640 import MLX90640, RefreshRate
from gps_v2 import SQTGPS
from triple_t import Comms
from triggering_v2 import SQTtrigger
from servo_2 import Servo
from helper import Helper
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
sd, vfs = helper.init_sd_card()  
file_list = helper.make_files()  
pressure_sensor, temp_sensor, frame_taker, gps_sensor, TTT, servo_motor = helper.init_sensors(file_list)   # init all sensors
triggering = SQTtrigger()  

#SETUP: setting all the flags, counters, and start of lists to use in main

trigger = False       # flag to trigger valve
trigger_condition = None      # to set trigger condition too so we know what message to send
counter = 1     # for timing transmitions
error_counter = 0
science_frame_count = 0  # for timing science frame transmisions
science_data = []
science_times = []
current_gps_data = [None, 'None', 'None', 'None', 99.99]
p_list = []
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
            tempE, tempI = temp_sensor.read_temp(file_list[2]) 

        except Exception as e:
            t = time.time()
            helper.log_error(t, e, "Temperature Sensor", file_list[2])

    #3. GPS
    
    if gps_sensor:
        time.sleep_ms(100)
        try:
            gps_data = gps_sensor.gps_log()
            
            if gps_data[1] == 'None':
                gps_data = current_gps_data # setting current_gps_data to the latest good string so if we stop getting position for a bit we use the last good values

            else:
                current_gps_data = gps_data
                
        except Exception as e:
            t = time.time()
            helper.log_error(t, e, "GPS Sensor", file_list[2])
        
    
    #4. Making a list of housekeeping data:
    
    house_list = helper.make_house_list(pressure_T, pressure_P, tempE, tempI, gps_data, file_list) 
    p_list, a_list = helper.update_a_p_lists(house_list, p_list, a_list)  # list for triggering, capped at the latest 12 values each
    
    #5. TRIGGER CHECK (only happends when trigger = False).
    
    if not trigger:
            
        trigger, condition, pres, alt = triggering.trigger_check(p_list[-1], a_list[-1], a_list, p_list, file_list)
        
        # only checks for trigger if it has not triggered yet:
        if trigger:
            
            #print(f"MEM ALOC PRE TRIGGER OPS: {gc.mem_alloc()}")   # uncomment to see if anything was collected
            gc.collect()
            #print(f"gc collect: {gc.collect()}")   # uncomment to see if anything was collected
            
            #1. change thermal sensor freq to handle quicker refresh rate
            frame_taker = helper.reinit_frame_taker(file_list, before = True)

            #2. run servo
            try:
                servo_motor.run_servo()
            except Exception as e:
                t = time.time()                
                helper.log_error(t, e, "Servo Activation", file_list[2])
            
            #3. get science frames:
            
            for i in range(16):
                # getting 16 science frames in a row right after the servo triggers:
                try:
                    science_frame = helper.init_float_array(768)
                    helper.get_full_frame(science_frame, frame_taker)
                    t = time.time()
                except Exception as e:
                    t = time.time()
                    helper.log_error(t, e, "MLX Science Acqui.", file_list[2])
     
                science_times.append(t)
                science_data.append(science_frame)
                
                print(f"CURRENT ME ALLOC: {gc.mem_alloc()}")
                
            helper.write_science_frames(science_data, science_times, file_list) # writes a file of times and a file of frames
            
            
            #4. change this i2c bus frequency back to what the pressure sensor and slower frame rate needs:
            frame_taker = helper.reinit_frame_taker(file_list, before = False)

    #6. Thermal Sensor
    time.sleep_ms(100)
    frame = helper.init_float_array(768)
    try:
        if frame_taker:
            t = time.time()
            helper.get_full_frame(frame, frame_taker)
            helper.write_frame(frame, t, file_list)
            
    except Exception as e:
        helper.log_error(time.time(), e, "Thermal Sensor", file_list[2])

    #7. Data downlinks: check counter for timing of science and telem packet sending (packets are also sent at loop 1 and 2)
    
    print(f"FREE MEMORY: {gc.mem_free()}")
    
    if TTT:
        if counter == 1 or counter % 8 == 0: 
            if not trigger:
                TTT.science_packet(trigger, condition, pres, alt, frame)
                del(frame)    # delete frame from pico memory after sending
                gc.collect()   
                
            elif trigger:
                try:
                    science_frame = science_data[science_frame_count % len(science_data)]
                    TTT.science_packet(trigger, condition, pres, alt, science_frame)
                except Exception as e:
                    helper.log_error(time.time(), e, "TTT Science post Trigger", file_list[2])
      
        if counter == 2 or counter % 5 == 0:
            error_counter = TTT.telem_packet(house_list, error_counter)   
            #print(f"what EC is set to: {error_counter}")  #uncomment if you want an indication of errors when running connected to computer
        
    #8. counting
    
    print(f'########LOOP COUNTER {counter} ###################')
    counter += 1
    
    if trigger:
        science_frame_count += 1
        
    time.sleep_ms(500)
