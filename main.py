from ms5611 import MS5611
from ds18b20 import DS18B20
from mlx90640 import MLX90640
from gps import SQTGPS
#from comms import Comms

import sdcard
import os
import time
import machine

from machine import Pin, SPI

SPI_BUS = 0
SCK_PIN = 2
MOSI_PIN = 3
MISO_PIN = 4
CS_PIN = 5
SD_MOUNT_PATH = '/sd'

file_list = [
    '/sd/trigger_log.txt',
    '/sd/ms5611_log.txt',
    '/sd/ds18b20_external_log.txt',
    '/sd/ds18b20_internal_log.txt',
    '/sd/mlx90640_log.txt',
    '/sd/gps_log.txt'
]


# Setup sd card
try:
    spi = SPI(SPI_BUS, baudrate=1320000, sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN), miso=Pin(MISO_PIN))
    cs = Pin(CS_PIN, Pin.OUT)
    cs.value(1)

except: print("SD card pin error")

sd = sdcard.SDCard(spi, cs)
os.mount(sd, SD_MOUNT_PATH)

try:
    # Initialize and mount SD
    sd = sdcard.SDCard(spi, cs)
    os.mount(sd, SD_MOUNT_PATH)

except: print('SD card mount error')

# Small delay before file ops
time.sleep_ms(50)

# Initalize files and write header information

try:
    for fname in file_list:
        with open(fname, 'w') as f:
            if 'ms5611' in fname:         # pressure
                f.write("Timestamp (s), Temperature (Celsius), Pressure (mbar)\n")
            elif 'ds18b20' in fname:       # should do both temperature files
                f.write("Timestamp, Temp (deg)\n")
            elif 'mlx90640' in fname:     # thermal sensor
                f.write("\n")
            elif 'gps' in fname:            # gps
                f.write("Timestamp (s), Lat (deg), Lon (deg), Alt (m)\n")
            elif 'trigger' in fname:
                f.write("Timestamp (s), Trigger, Trigger Condition\n")
                f.write(f"{time.time()}, False, None \n")                 # trigger set to false to begin with 
            else:
                print('file names incorrect')
except:
    print('SD card file writing error')

# sensor setup:

try:
    pressure_sensor = MS5611(i2c_bus=0, sda_pin=8, scl_pin=9)
except:
    pressure_sensor = None
    print("Pressure Sensor Error")

try:
    temp_sensor_i = DS18B20(pin=21) # internal temp, same actions but to a diff pin
except:
    temp_sensor_i = None
    print("Temperature Sensor Error")
    
try:
    temp_sensor_e = DS18B20(pin=19)    # external temp, same actions but to a diff pin
except:
    temp_sensor_e = None
    print("Temperature Sensor Error")

try:
    frame_taker = MLX90640(i2c=0, address=0x33, sda_pin=16, scl_pin=17)
except:
    frame_taker = None
    print("MLX90640 Sensor Error")
    
try:
    gps_sensor = SQTGPS(uart = 0, baudrate = 9600, tx_pin = 12, rx_pin = 13)
except:
    gps_sensor = None
    print("GPS Sensor Error")


# Data loop

trigger = False # set this variable here too 
servo_activated = False # flags that servo has or hasnt activated
#counter = 0

for _ in range(5):  
    
    #1. pressure:
    if pressure_sensor:
        T_val = pressure_sensor.read_adc('T')
        P_val = pressure_sensor.read_adc('P')
        
        if T_val and P_val:
            T_E, P = pressure_sensor.compute_pressure(T_val, P_val)

        else:
            print("MS5611 failed")
        try:
            pressure_sensor.log_pressure(file_list[1])
        except: print('Pressure not logged')
    
    #2. gps
    if gps_sensor:
        try:
            print(gps_sensor._listen_for_sequence())
            gps_sensor.gps_log(file_list[5])
        except: print('GPS not logged')      
    
    #3. trigger check:
    
    if gps_sensor and pressure_sensor:
        try:
            print('woulda done the trigger check here')
            # trigger = run action, will return true or false, and condition written to file
            #should also make variable true or false
            
            #trigger, condition = SQTRtrigger.trigger_algorithm(file_list[1], file_list[5])
        except: print('Trigger not logged')
    
    #if trigger is true and servo_activated is False, activate servo
    if trigger == True and servo_activated == False:
        
        try:
            print('woulda activated servo here')
            #servo.activate_servo()
            #servo_activated = True
        except:
            print('servo activation error')

    
    #4. thermal sensor
        
    if frame_taker:
        try:
            frame_taker.mlx_log(file_list[4])
        except: print('Thermal Sensor not logged')
    
    #5. temp sensors:
        
    if temp_sensor_i:
        
        try:
            temp_sensor_i.log_temp(file_list[4])
        except: print('Internal Temp not logged')
    
    if temp_sensor_e:
        try:
            temp_sensor_e.log_temp(file_list[3])
        except: print('External Temp not logged')
        
    #6. comms:

    

# unmounting sd card after looping 5 times
os.umount(SD_MOUNT_PATH)
#-------------------------- Data Downlink-----------------------------------------------------
#    if counter%10==0 and counter%3==0:
 #      Comms.data_packet()
#  
#    elif counter%10==0:
#       Comms.telem_packet()
#
#    counter += 1
   
#    time.sleep_ms(200)
