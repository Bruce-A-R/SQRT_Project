from ms5611 import MS5611
from ds18b20 import DS18B20
from mlx90640 import MLX90640
from gps import GPS
from comms import Comms

import os
import time
import machine

from machine import SPI, Pin
import sdcard, os

# -----------------------------SD CARD SETUP--------------------------------
SPI_BUS = 0
SCK_PIN = 2
MOSI_PIN = 3
MISO_PIN = 4
CS_PIN = 5
SD_MOUNT_PATH = '/sd'

file_list = ['/sd/trigger_log.txt', '/sd/ms5611_log.txt', '/sd/ds18b20_log.txt', '/sd/mlx90640_log.txt', '/sd/gps_log.txt']
   
try:
    spi = SPI(SPI_BUS,sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN), miso=Pin(MISO_PIN))
    cs = Pin(CS_PIN)
    sd = sdcard.SDCard(spi, cs)
    
    # Mount microSD card
    os.mount(sd, SD_MOUNT_PATH)
    
except:
    print('SD card Pin Error')

#------------------------Textfile Initialisation----------------------------
try:
    for file in file_list:
        os.remove(file)
    
    
    with open(file_list[0], "w") as file:                      # trigger log file
        file.write("Timestamp (s), Trigger, Trigger Condition \n")
    
    with open(file_list[1], "w") as file:                      # pressure file
        file.write("Timestamp (s), Temperature (Celsius), Pressure (mbar) \n")
    
    with open(file_list[2], "w") as file:                      # thermometer file
        file.write("Timestamp, Temp (deg)\n")
    
    with open(file_list[3], "w") as file:                     # thermal sensor file
        file.write("\n")
    
    with open(file_list[4], "w") as file:                     # gps file
        file.write("Timestamp (s), Lat (deg), Lon (deg), Alt (m)\n")

except: print("SD card error")

# --------------------------- Sensor Setup -------------------------------
try:
    pressure_sensor = MS5611(i2c_bus=0, sda_pin=8, scl_pin=9)
except:
    pressure_sensor = None
    print("Pressure Sensor Error")

try:
    temp_sensor = DS18B20(pin=21)
except:
    temp_sensor = None
    print("Temperature Sensor Error")

try:
    frame_taker = MLX90640(i2c_bus=1, sda_pin=14, scl_pin=15)
except:
    frame_taker = None
    print("MLX90640 Sensor Error")
    
try:
    gps_sensor = GPS(uart tx_pin = , rx_pin = )
    
except:
    gps_sensor = None
    print("GPS Sensor Error")


# ------------------- Data Acquisition -------------------------------------
counter = 0
while True:

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
        
    if temp_sensor:
        
        try:
            temp_sensor.log_temp(file_list[2])
        except: print('Temp not logged')

    
    if frame_taker:
        frame_taker.mlx_log(file_list[3])

    if gps_sensor:
        gps_sensor.gps_log(file_list[4])
        
#-------------------------- Data Downlink-----------------------------------------------------
    if counter%10==0 and counter%3==0:
       Comms.data_packet()
  
    elif counter%10==0:
       Comms.telem_packet()

    counter += 1
       
       
