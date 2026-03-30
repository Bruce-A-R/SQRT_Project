"""
main_v3.py

version 3 of main function with triggering and servo included included


This version still includes our old file system (individual files for each sensor)


"""
# The classes for each subsystem are imported
from ms5611 import MS5611                               # Pressure Sensor
from ds18b20 import DS18B20                             # Temperature Sensors
from mlx90640 import MLX90640, RefreshRate              # Thermal Sensor/Camera
from gps_v2 import SQTGPS                               # GPS Sensor
from triple_t import Comms                              # Communications 
from triggering import SQTtrigger as triggering         # Triggering Algorithm
from servo import Servo                                 # Servo Motor (El Nueve)

#import sdcard
import sdcard_v2 as sdcard        # using second version of sdcard class from adafruit forums
import uos as os 
import time
import machine
import array
import struct
import math

from machine import Pin, SPI

# SETUP TASKS, first the sd card
SPI_BUS = 1
SCK_PIN = 10
MOSI_PIN = 11
MISO_PIN = 12
CS_PIN = 13
SD_MOUNT_PATH = '/sd'

file_list = [
    '/sd/trigger_log.txt',
    '/sd/ms5611_log.txt',
    '/sd/ds18b20_log.txt',
    '/sd/mlx90640_log.txt',
    '/sd/gps_logger.txt',
    '/sd/mlx90640_science.txt'
]

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
except: print('pin error')

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
    
    print('mounted sd?')
    
except Exception as e: print(f"mounting error: {e}")



try:

    # Small delay before file ops
    time.sleep_ms(50)

    # If a file of the same name is on the SD card, it is removed before being re-initialised.
    for file in file_list:
        try:
            os.remove(file)
        
        except OSError:
            pass

    # Initialize log files safely
    for fname in file_list:
        with open(fname, 'w') as f:
            if 'ms5611' in fname:
                f.write("Timestamp (s), Temperature (Celsius), Pressure (mbar)\n")
            elif 'ds18b20' in fname:
                f.write("Timestamp, TempE(deg), TempI(deg)\n")
            elif 'mlx90640' in fname:
                f.write("MLX90640 Raw Data Values")
            elif 'gps' in fname:
                f.write("Timestamp (s), Lat (deg), Lon (deg), Alt (m), HDOP \n")
            else:
                f.write("Timestamp (s), Trigger, Trigger Condition, Pressure, Altitude \n")

except Exception as e:
    print("Files not initialised", e)

# MORE SETUP: initializing sensors

try:
    pressure_sensor = MS5611(i2c_bus=0, sda_pin=4, scl_pin=5, address = 0x77)
except:
    pressure_sensor = None
    print("Pressure Sensor Error")

#try:
temp_sensor = DS18B20(pin=21)

if not temp_sensor.available:
    print("Temperature Sensor Error")
    temp_sensor = None

#except Exception as e:
#temp_sensor = None
#print("Temperature Sensor Error:", e)



try:
    frame_taker = MLX90640(i2c=0, address=0x33, sda_pin=4, scl_pin=5)
    frame_taker.refresh_rate = RefreshRate.REFRESH_8_HZ
except:
    frame_taker = None
    print("MLX90640 Sensor Error")
    

  
try:
    gps_sensor = SQTGPS(uart_bus = 1, baudrate = 9600, tx_pin = 8, rx_pin = 9)
except:
    gps_sensor = None
    print("GPS Sensor Error")
#print(os.listdir("/sd"))

try:
    TTT = Comms(address = 0x53, callsign = "SQRT", uart_bus=0, tx_pin = 0, rx_pin = 1)

except:
    TTT = None
    print("T-cubed Error")
    




# LAST SETUP: setting all the flags and counters

trigger = False       # flag to trigger valce
trigger_condition = None      # to set trigger condition too so we know what message to send
counter = 0     # for timing transmitions



# THE MAIN LOOP:

for _ in range(50):


    # 1. pressure sensor
    
    time.sleep_ms(100)
    if pressure_sensor:
        T, P = pressure_sensor.log_pressure()
        t = time.time()


        try:
            time.sleep_ms(1000)
            with open(file_list[1], "a") as f:
                if T == None or P == None:
                    f.write(f"{t}, NaN, NaN \n")
                else:
                    
                    f.write(f"{t}, {T},{P} \n")
        except Exception as e:
            print("the end: ,", e)


    #2. GPS

    if gps_sensor:
                gps_data = gps_sensor.gps_log()
                if gps_data: 

                    with open(file_list[4], 'a') as file:
                        file.write(f"{gps_data[0]}, {gps_data[1]}, {gps_data[2]}, {gps_data[3]}, {gps_data[4]} \n")
                else:
                    with open(file_list[4], 'a') as file:
                        file.write("NaN, NaN, NaN, NaN, NaN \n")
        #except Exception as e:
            #print("GPS not logged:", e)



    #3. TRIGGER CHECK (only happends when trigger = False). if true, servo imediately activated. 
    def init_float_array(size) -> array.array:
        return array.array('f', (0 for _ in range(size)))
    science_frame = init_float_array(768)
    
    if not trigger:
        p_dict, gps_dict = triggering._parse_files_triggering(file_list[1], file_list[4])

        trigger, condition, pres, alt = triggering.trigger_check(p_dict, gps_dict)
        
        t = time.time()
        with open(file_list[0], "a") as f:
            f.write(f"{t}, {trigger}, {condition}, {pres}, {alt} \n")
        
        if trigger:
            Servo.activate_servo(pin = 22)
            
            science_frame = init_float_array(768)
            
            frame_taker.get_frame(science_frame)
            t = time.time()
            
            with open(file_list[5], "a") as f:
                f.write(f"{t}")
                for temp in science_frame:
                    f.write(f"{temp},")
                f.write("\n")
            
            


    #4. Thermal Sensor
    def init_float_array(size) -> array.array:
        return array.array('f', (0 for _ in range(size)))

    if frame_taker:
        frame = init_float_array(768)
        frame_taker.get_frame(frame)
        t = time.time()

        with open(file_list[3], "a") as f:
            f.write(f"{t}")
            for temp in frame:
                f.write(f"{temp},")
            f.write("\n")      

         #   print("Thermal Array not logged", e)

    time.sleep_ms(100)       
        
    #5. temperature sensors (internal and external)

    if temp_sensor:
        try:
            temp_sensor.log_temp(file_list[2])
            
        except Exception as e:
            print("Temperature not logged", e)

    time.sleep_ms(100)


    #6. Data downlinks: check counter for timing of science and telem packet sending

    if TTT:
        if counter % 18 == 0: 
            print("Sending science packet")
            TTT.science_packet()
            
        if counter % 10 == 0:
            print("Sending telemetry packet")

            TTT.telem_packet()

    
    counter += 1
           
    time.sleep(1)

