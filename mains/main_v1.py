"""
main.py

first version of the main function with a data collection loop

"""






from ms5611 import MS5611
from ds18b20 import DS18B20
from mlx90640 import MLX90640
from gps import SQTGPS
from triple_t import Comms
#from comms import Comms

#import sdcard
import sdcard_v2 as sdcard        # using second version of sdcard class from adafruit formus but it STILL DOESNT WORK
import uos as os
import time
import machine

from machine import Pin, SPI

SPI_BUS = 1
SCK_PIN = 10
MOSI_PIN = 11
MISO_PIN = 12
CS_PIN = 13
SD_MOUNT_PATH = '/sd'

file_list = [
    '/sd/trigger_log.txt',
    '/sd/ms5611_log.txt',
    '/sd/ds18b20_external_log.txt',
    '/sd/ds18b20_internal_log.txt',
    '/sd/mlx90640_log.txt',
    '/sd/gps_log.txt'
]

try:
    # Assign chip select (CS) pin 
    cs = machine.Pin(CS_PIN, machine.Pin.OUT)

    # Intialize SPI peripheral (start with 1 MHz)
    spi = machine.SPI(SPI_BUS,
                      baudrate=1000000,
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
                f.write("Timestamp, Temp (deg)\n")
            elif 'mlx90640' in fname:
                f.write("MLX90640 Raw Data Values")
            elif 'gps' in fname:
                f.write("Timestamp (s), Lat (deg), Lon (deg), Alt (m)\n")
            else:
                f.write("Timestamp (s), Trigger, Trigger Condition\n")

except Exception as e:
    print("Files not initialised", e)



# --------------------------- Sensor Setup -------------------------------
try:
    pressure_sensor = MS5611(i2c_bus=0, sda_pin=4, scl_pin=5)
except:
    pressure_sensor = None
    print("Pressure Sensor Error")

try:
    temp_sensor = DS18B20(pin=22)

    if not temp_sensor.available:
        print("Temperature Sensor Error")
        temp_sensor = None

except Exception as e:
    temp_sensor = None
    print("Temperature Sensor Error:", e)


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

try:
    TTT = Comms(address = 0x53, callsign = "SQT", uart_bus=0, tx_pin = 0, rx_pin = 1)

except:
    TTT = None
    print("T-cubed Error")

# ------------------- Data Acquisition -------------------------------------
counter = 0
comms = Comms()
for _ in range(50):  

    if pressure_sensor:
        try:
            pressure_sensor.log_pressure(file_list[1])
        except Exception as e: print('Pressure not logged', e)
        
    if temp_sensor:
        try:
            temp_sensor.log_temp(file_list[2])
        except Exception as e:
            print("Temperature not logged", e)


    
    if frame_taker:
        try:
            frame_taker.mlx_log(file_list[3])
        except:
            print("Thermal Array not logged")

  
    if gps_sensor:
        try:
            # Attempt to read for only 100 ms
            data = gps_sensor._listen_for_sequence(timeout=1000)  
            if data:
                gps_sensor.gps_log(file_list[4])
            else:
                print("No GPS data available this loop")
        except Exception as e:
            print("GPS not logged:", e)


#-------------------------- Data Downlink-----------------------------------------------------
    if TTT:
        if counter % 10 == 0:
            print("Sending science packet")
            comms.science_packet()
            
        if counter % 6 == 0:
            print("Sending telemetry packet")

            TTT.telem_packet()

    
    counter += 1
           
    time.sleep(1)
