"""
version 8 of main function with triggering and servo included included

Overview of main function (2/4/2026 CK and BR)

this main has an updated file system:
-all housekeeping data is saved to one file
-all raised errors saved to an error log
-trigger check information is saved to a trigger log
-thermal sensor frames saved to two seperate logs:
    - background frames saved to data_log
    - frames taken immediately after trigger (in the quick burst of sensor captures) saved to post_trigger_data_log
- helper function to take stuff out of main
- still a lot of imports 
    

Loop actions sequence:
1. take housekeeping data
    - save list of most recent 12 pressure and altitude values for the triggering checks
2. check for trigger conditions, then activate servo and take quick burst of frames if triggered
3. check for timing for transmissions. If timing is right for science or telemetry packages, send them
    - what is sent will depend on wether the valve has triggered and there are post-trigger frames to send or not
    - delete frames (not the burst imediately post-trigger) after sending to free up memory. The post
      trigger burst is saved so that we can retransmit and mitigate loss from missed transmissions.

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
current_gps_data = [time.time(), 'None', 'None', 'None', 99.99]

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
            
            if gps_data[1] != 'None':
                current_gps_data = gps_data   # setting current_gps_data to the latest good string so if we stop getting position for a bit we use the last good values

        except Exception as e:
            t = time.time()
            helper.log_error(t, e, "GPS Sensor", file_list[2])
            
    
    #4. Making a list of housekeeping data:
    house_list = helper.make_house_list(pressure_T, pressure_P, tempE, tempI, current_gps_data, file_list) 
    p_list, a_list = helper.update_a_p_lists(house_list, p_list, a_list)  #list for triggering, capped at the latest 12 values each
    

    
    #5. TRIGGER CHECK (only happends when trigger = False).
    
    if not trigger:
        
        # checking (and logging) triggering conditions
        trigger, condition, pres, alt = triggering.trigger_check(p_list[-1], a_list[-1], a_list, p_list, file_list)
        
        # only checks for trigger if it has not triggered yet:
        if trigger:
            
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
        time.sleep_ms(100) 
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
            helper.log_error(time.time(), e, "Thermal Sensor", file_list[2])

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
                    helper.log_error(time.time(), e, "TTT Science post Trigger", file_list[2])
      
        if counter == 2 or counter % 6 == 0:
            print("Sending telemetry packet")
            
            try:
                error_counter = TTT.telem_packet(house_list, error_counter)
            except Exception as e:
                helper.log_error(time.time(), e, "TTT Telem", file_list[2])
                
            print(f"what EC is set to: {error_counter}")

        
    print(f'########LOOP COUNTER {counter} ###################')
    
    #8. counting:
    counter += 1
    
    if trigger:
        science_frame_count += 1
    
    time.sleep_ms(500)
