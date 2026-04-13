"""
main.py

Authors: Bruce Ritter, Caimin Keavney
Version Date: 13/4/2026

Description:

Main function that runs automatically when Pico connected to power. 
Actions in the loop sequence are marked with a commented and numbered line (ex: #1. _____ action)

#####TEST CODE STILL INCLUDED#####
There is commented out values used to test A-G tests of triggering algorithm using simulated
pressure and altitude data. These are left in to use in long range test if applicable.
DO NOT UNCOMMENT.
test code is only within the ########## line brackets, and will be removed once testing is concluded. 
##################################

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
            
            if gps_data[1] == 'None':
                gps_data = current_gps_data # setting current_gps_data to the latest good string so if we stop getting position for a bit we use the last good values

            else:
                current_gps_data = gps_data
                
        except Exception as e:
            t = time.time()
            helper.log_error(t, e, "GPS Sensor", file_list[2])
        
    
    #4. Making a list of housekeeping data:
    house_list = helper.make_house_list(pressure_T, pressure_P, tempE, tempI, gps_data, file_list) 
    p_list, a_list = helper.update_a_p_lists(house_list, p_list, a_list)  #list for triggering, capped at the latest 12 values each
    
    #5. TRIGGER CHECK (only happends when trigger = False).
    
    ################### FOR TRIGGERING CHECKS< REMOVE BEFORE FLIGHT########################
    if counter == 2:
        #different lists we can use to check:
        #p_list = [1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000]
        #p_list = ["None", "None", "None", "None", "None", "None", "None", "None", "None", "None", "None", "None"]
        #p_list = []
        p_list = [1000, 500, 400, 300, 200, 100, 50, 40, 60, 55, 40, 30]  #pressure check should check true
        #p_list = [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 20000, 20100] #pressure sensor good but check false
        
        #a_list = [1000, 1000, 1500, 1400, 1500, 1510, 1520, 1530, 1540, 1550, 1560, 1570] # data good but should check false
        #a_list = [2000, 4000, 5000, 6000, 7000, 1200, 1300, 1500, 1600, 20000, 23000, 23000]   #altitude should check true
        a_list = [2000, "None", 5000, 6000, 7000, "None", 1300, 1500, 1600, 20000, 23000, 23000]
        #a_list = [22000, 21000, 21100, "None", 20000, 19000, 18000, 18010, 18010, 18000, 17500, 17450] #falling check should check true
            

    #######################################################################################
    if not trigger:
            
        trigger, condition, pres, alt = triggering.trigger_check(p_list[-1], a_list[-1], a_list, p_list, file_list)
        
        # only checks for trigger if it has not triggered yet:
        if trigger:
            
            
            try:
                del(frame)    #trying to clear memory
                gc.collect()
            except: pass
            
            gc.collect()
            print(f"gc collect: {gc.collect()}")
            
            #1. change thermal sensor freq to handle quicker refresh rate
            frame_taker = helper.reinit_frame_taker(file_list, before = True)
            #machine.freq(1000000)
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
                    helper.get_full_frame(science_frame, frame_taker)
                except Exception as e:
                    #writing error to error log
                    t = time.time()
                    helper.log_error(t, e, "MLX Science Acqui.", file_list[2])
     
                
                science_times.append(t)
                science_data.append(science_frame)
                
            helper.write_science_frames(science_data, science_times, file_list) # writing the frames to a file with the times associated
            
            
            #4. change this i2c bus frequency back to what the pressure sensor and slower frame rate needs:
            frame_taker = helper.reinit_frame_taker(file_list, before = False)
            #machine.freq(400000)

    #6. Thermal Sensor
    time.sleep_ms(100)
    frame = helper.init_float_array(768)
    try:
        if frame_taker:
            
            t = time.time()
            helper.get_full_frame(frame, frame_taker)
            try:
                with open(file_list[1], "a") as f:
                    f.write(f"{t} FRAME DATA: \n")
                    for temp in frame:
                        f.write(f"{temp},")
                    f.write("\n")
            except Exception as e:
                helper.log_error(time.time(), e, "Thermal Sensor File Write", file_list[2])
            
    except Exception as e:
        helper.log_error(time.time(), e, "Thermal Sensor", file_list[2])

    #7. Data downlinks: check counter for timing of science and telem packet sending
    
    print(f"FREE MEMORY: {gc.mem_free()}")
    
    if TTT:
        if counter == 1 or counter % 8 == 0: 
            print("Sending science packet")
            
            if not trigger:
                TTT.science_packet(trigger, condition, pres, alt, frame)
                
                del(frame)    # delete frame from pico memoery after sending
                gc.collect()
                
            elif trigger:
                
                try:
                    science_frame = science_data[science_frame_count % len(science_data)]
                    TTT.science_packet(trigger, condition, pres, alt, science_frame)
                except Exception as e:
                    helper.log_error(time.time(), e, "TTT Science post Trigger", file_list[2])
      
        if counter == 2 or counter % 5 == 0:
            print("Sending telemetry packet")
            
            error_counter = TTT.telem_packet(house_list, error_counter)

                
            print(f"what EC is set to: {error_counter}")

        
    print(f'########LOOP COUNTER {counter} ###################')
    
    #8. counting:
    counter += 1
    
    if trigger:
        science_frame_count += 1
    
    time.sleep_ms(500)
