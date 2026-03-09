"""
main.py

Main loop to run on SQRT onboard computer



"""


from ms5611 import MS5611
from ds18b20 import DS18B20
from mlx90640 import MLX90640

import time
import machine

from machine import SPI, Pin
import sdcard, os




# setup tasks: files on sd card: 

# SD CARD SETUP:
SPI_BUS = 0
SCK_PIN = 2
MOSI_PIN = 3
MISO_PIN = 4
CS_PIN = 5
SD_MOUNT_PATH = '/sd'

file_list = ['sd/trigger_log.txt', 'sd/ms5611_log.txt', 'sd/ds18b20_log.txt', 'sd/mlx90640_log', 'sd/gps_log']
   
try:
    spi = SPI(SPI_BUS,sck=Pin(SCK_PIN), mosi=Pin(MOSI_PIN), miso=Pin(MISO_PIN))
    cs = Pin(CS_PIN)
    sd = sdcard.SDCard(spi, cs)
    # Mount microSD card
    os.mount(sd, SD_MOUNT_PATH)
    
    with open(file_list[0], "w") as file:                      # trigger log file
        write("Timestamp (s), Trigger, Trigger Condition \n")
    
    with open(file_list[1], "w") as file:                      # pressure file
        write("Timestamp (s), Pressure (centi mbar), Temperature (centi Celsius) \n")
    
    with open(file_list[2], "w") as file:                      # thermometer file
        write("Timestamp, Temp (deg)")
    
    with open(file_list[3], "w") as file:                     # thermal sensor file
        write("\n")
    
    with open(file_list[4], "w") as file:                     # gps file
        write("Timestamp (s), Lat (deg), Lon (deg), Alt (m)\n")

except: print("ruh roh SD card error")

# pressure sensor:
try:
    pressure_sensor = MS5611(i2c_bus=1, sda_pin=6, scl_pin=7)    

except:
    pressure_sensor = None
    print("Pressure Sensor Error")

# temp sensor:
try:
    temp_sensor = DS18B20(pin=21)
except:
    temp_sensor = None
    print("Temperature Sensor Error")

# thermal sensor
try:
    frame_taker = MLX90640(i2c_bus=1, sda_pin=14, scl_pin=15)
except:
    frame_taker = None
    print("MLX90640 Failure")

# gps
try:
    #gps_sensor = SQRTGPS(UART_bus = 0, TX =, RX = ) #UART(0, baudrate =9600 , tx=Pin(12), rx=Pin(13))
except:
    gps_sensor = None 
    print("GPS Failure")


# antenna



# servo motor



# DATA COLLECTION LOOP:

while True:
    if pressure_sensor:
        T_val = pressure_sensor.read_adc('T')
        P_val = pressure_sensor.read_adc('P')
        
        
        
        if T_val and P_val:
            T_E, P = pressure_sensor.compute_pressure(T_val, P_val)
            print(T_E, P)
            
        else:
            print("MS5611 failed")
        
        pressure_sensor.log_pressure()
        
        
    if temp_sensor:
        T_int = temp_sensor.read_temp()
        
        if T_int is not None:
            print(f"T_int:{T_int}")
            
        else:
            print("DS18B20 failed")
        
        temp_sensor.log_temp()
    

    if frame_taker:
        frame_taker.mlx_log()

    time.sleep(5)
