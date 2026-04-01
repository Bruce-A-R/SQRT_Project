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
import sdcard_v2 as sdcard        # using second version of sdcard class from adafruit forums
import uos as os
import time
import machine
import array
import struct
import math
import random

from machine import Pin, SPI

#SETUP: first initialize helper:

helper = Helper()

# SETUP TASKS, first the sd card

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

# mounting SD card

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
    except Exception as e:
        print("mount fail", e)
    
    print(f'SD card mounted at time: {time.time()}')
    
except Exception as e:
    
    print(f"mounting error: {e}")

# SETUP: making files (and keeping the error log file path to use elsewhere)
file_list = helper.make_files()

# MORE SETUP: initializing sensors

# Pressure Sensor
try:
    pressure_sensor = MS5611(i2c_bus=0, sda_pin=4, scl_pin=5, address = 0x77)
except Exception as e:
    pressure_sensor = None
    helper.log_error(time.time(), e, "Pressure Sensor Init", error_log)

#Temperature Sensor(s)
try:
    temp_sensor = DS18B20(pin=21)
except: 
    print("Temperature Sensor Error")
    temp_sensor = None
    helper.log_error(time.time(), e, "Temp Sensor(s) Init", file_list[2])

# Thermal Sensor
try:
    frame_taker = MLX90640(i2c=0, address=0x33, sda_pin=4, scl_pin=5)
    frame_taker.refresh_rate = RefreshRate.REFRESH_8_HZ                 # currently the fasted refresh rate that doesn't kill itself,
                                                                        # reason unclear and seen by many users of the product online
except Exception as e:
    frame_taker = None
    print("MLX90640 Sensor Error")
    helper.log_error(time.time(), e, "MLX Sensor Init", file_list[2])

# GPS 
try:
    gps_sensor = SQTGPS(uart_bus = 1, baudrate = 9600, tx_pin = 8, rx_pin = 9)
except exception as e:
    gps_sensor = None
    print("GPS Sensor Error")
    helper.log_error(time.time(), e, "GPS Init", file_list[2])
    
# Communications
try:
    TTT = Comms(file_list, address = 0x53, callsign = "SQRT", uart_bus=0, tx_pin = 0, rx_pin = 1)

except Exception as e:
    TTT = None
    print(f"T3 Error: {e}")
    helper.log_error(time.time(), e, "TTT Init", file_list[2])

#initializing servo:
try:
    servo_motor = Servo()
except Exception as e:
    print("Servo initialization error")
    helper.log_error(time.time(), e, "Servo Init", file_list[2])
    
#initializing triggering class, should just always happen since there's no sensor to connect with but why not add a try/except clause

triggering = SQTtrigger()

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

# defining initiating float array for thermal sensor
def init_float_array(size) -> array.array:
    """Function to make a float array for the thermal sensor
    Notes: This for some reason wasn't working as a function defined and used in the MLX class,
    so we're defining it here
    Input: array size
    Output: array of 0s
    """
    return array.array('f', (0 for _ in range(size)))

# THE MAIN LOOP:

while True:


    # 1. pressure sensor
    
    time.sleep_ms(100)
    if pressure_sensor:
        
        try:
            pressure_T, pressure_P = pressure_sensor.log_pressure()
            t = time.time()

            time.sleep_ms(500)  #changed from 1000
        
        except Exception as e:
            #print("the end: ,", e)
                
            #writing error to error log
            
            try:
                with open(file_list[2], "a") as file:
                    file.write(f"{time.time()}, {e}, Pressure Sensor \n")
            except: pass
    #2. temperature sensors (internal and external)

    if temp_sensor:
        try:
            #temp_sensor.log_temp(file_list[0])
            tempE, tempI = temp_sensor.read_temp(file_list[2])  # recently swaped tempE and tempI cuz I think I had them backwards
            
        except Exception as e:
            print("Temperature not logged", e)
            
            #writing error to error log
            try:
                with open(file_list[2], "a") as file:
                    file.write(f"{time.time()}, {e}, Temp Sensors \n")
            except: pass

    time.sleep_ms(100)
        


    #3. GPS

    if gps_sensor:
        try:
            gps_data = gps_sensor.gps_log()
            
            #if this returns Nones, it is currently being handled down the line

        except Exception as e:
            print("GPS not logged:", e)
            
            try:
                with open(file_list[2], "a") as file:
                    file.write(f"{time.time()}, {e}, GPS \n")
            except: pass  

    #4. Writing Housekeeping data to the housekeeping file:
        
    # assigning null values if there is no data collected this loop
    if not pressure_T:
        pressure_T = 'None'
    if not pressure_P:
        pressure_P = 'None'
    if not tempI:
        tempI = 'None'
    if not tempE:
        tempE = 'None'
    if not gps_data:
            gps_data = current_gps_data
    elif len(gps_data) != 5:                 # in case some value is missing
        diff = 5 - len(gps_data)
        
        for i in diff:
            gps_data.append(99.99)
        
    #writing to file:
    # Keys: Timestamp, ms5611 Temperature (C), Pressure (mbar), TempE (deg), TempI (deg), Lat (deg), Lon (deg), Alt (m), HDOP 
    house_list = [time.time(), pressure_T, pressure_P, tempE, tempI, gps_data[0], gps_data[1], gps_data[2], gps_data[3], gps_data[4]]
    
    p_list.append(house_list[2])
    a_list.append(house_list[8])
    
    current_gps_data = gps_data #setting current_gps_data to the latset good string (or the baseline Nones)
    
    try:
        with open(file_list[0], "a") as file:
            file.write(f"{time.time()}, {pressure_T}, {pressure_P}, {tempE}, {tempI}, {gps_data[1]}, {gps_data[2]}, {gps_data[3]}, {gps_data[4]} \n") 
    except Exception as e:
        try:
            with open(file_list[2], "a") as file:
                file.write(f"{time.time()}, {e}, Writing Housekeeping to SD \n")
        except:
            print("couldn't write anything to file")

    #5. TRIGGER CHECK (only happends when trigger = False).
    
    print(trigger)
    
    if not trigger:
        
        try:      # trying to run trigger check
            #if counter == 5:
            #    trigger, condition, pres, alt = triggering.trigger_check(30, house_list[8], a_list, p_list, file_list[2])
            #else:
                
            trigger, condition, pres, alt = triggering.trigger_check(house_list[2], house_list[8], a_list, p_list, file_list[2])
            t = time.time()
            
            print(f"TRIGGER FROM CHECK: {trigger}, {condition}, {pres}, {alt}")
            
            try:            # just in case the SD card dies, put in try/except
                with open(file_list[3], "a") as f:
                    f.write(f"{t}, {trigger}, {condition}, {pres}, {alt} \n")
            except: pass
        
        except:  # keeps trigger and condition false in case of errors (may not be needed)
            trigger = False
            condition = None
            pres = house_list[2]
            alt = house_list[8]
        
        
        #if counter > 50:
        #    trigger = True
        
        if trigger: #and counter > 50:
            
            # 1. change thermal sensor freq to handle quicker refresh rate
            
            try:
                frame_taker = MLX90640(i2c=0, address=0x33, sda_pin=4, scl_pin=5, freq = 1000000)
                frame_taker.refresh_rate = RefreshRate.REFRESH_8_HZ                 
                                                                                    
            except Exception as e:
                frame_taker = None
                print(f"MLX90640 Sensor Error: {e}")
                
                # writing error to error log
                try:
                    with open(file_list[2], "a") as file:
                        file.write(f"{time.time()}, {e}, Thermal Sensor \n")
                except: pass

            
            #2. run servo
            try:
                servo_motor.run_servo()
            except Exception as e:
                print(f"servo motor connection exception: {e}")
                
                try:
                    with open(file_list[2], "a") as file:
                        file.write(f"{time.time()}, {e} during triggering, Servo \n")
                except: pass
            
            #3. get science frames:
            
            for i in range(8):
                # getting 54 science frames in a row right after the servo triggers
                #try:
                science_frame = init_float_array(768)
                
                frame_taker.get_frame(science_frame)
                #except Exception as e:
                #    print(f"frame taker exception: {e}")
                #                    #writing error to error log
                #    with open(file_list[2], "a") as file:
                #        file.write(f"{time.time()}, {e}, Thermal Sensor \n")
        
                #	science_frame = [0]
                
                t = time.time()
                print(t)
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
            try:
                frame_taker = MLX90640(i2c=0, address=0x33, sda_pin=4, scl_pin=5, freq = 400000)
                frame_taker.refresh_rate = RefreshRate.REFRESH_8_HZ                 
                                                                                    
            except Exception as e:
                frame_taker = None
                print("MLX90640 Sensor Error")
                
                # writing error to error log
                try:
                    with open(file_list[2], "a") as file:
                        file.write(f"{time.time()}, {e}, Thermal Sensor \n")
                except: pass


    #6. Thermal Sensor
    for _ in range(2): #take two pics to fill out checkerboard
        try:
            if frame_taker:
                frame = init_float_array(768)
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
        if counter % 3 == 0: 
            print("Sending science packet")
            
            if not trigger:
                TTT.science_packet(trigger, condition, pres, alt, frame)
            elif trigger and counter > 50:
                
                try:
                    science_frame = science_data[science_frame_count % len(science_data)]
                    TTT.science_packet(trigger, condition, pres, alt, science_frame)
                except Exception as e:
                    try:
                        with open(file_list[2], "a") as file:
                            file.write(f"{time.time()}, {e}, Thermal Sensor \n")
                    except: pass
                        
                
                
        if counter % 2 == 0:
            print("Sending telemetry packet")

            error_counter = TTT.telem_packet(house_list, error_counter)
            
            print(f"what EC is set to: {error_counter}")

        
    print(f'########LOOP COUNTER {counter} ###################')
    counter += 1
    
    if trigger:
        science_frame_count += 1
    time.sleep(1)
