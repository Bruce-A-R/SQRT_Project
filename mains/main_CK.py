"""
version 5 of main function with triggering and servo included included

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


from ms5611 import MS5611
from ds18b20 import DS18B20
from mlx90640 import MLX90640, RefreshRate
from gps_v2 import SQTGPS
from triple_t import Comms
from triggering import SQTtrigger
from servo_2 import Servo

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



# SETUP TASKS, first the sd card

SPI_BUS = 1
SCK_PIN = 10
MOSI_PIN = 11
MISO_PIN = 12
CS_PIN = 13
SD_MOUNT_PATH = '/sd'

n = str(random.randint(1,10000))

#new file system with less files: all housekeeping data, all science data, an error log

file_list = [
    '/sd/housekeeping_log' + n  + '.csv',
    '/sd/data_log' + n + '.csv',
    '/sd/error_log' +n + '.csv',
    '/sd/trigger_log' + n + '.csv',
    '/sd/post_trigger_data_log' + n + '.csv'     # to specifically hold frames taken imediately after trigger for ease of transmitting them 
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
except:
    print('pin error')
    
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
    
except Exception as e: print(f"mounting error: {e}")



try:

    # Small delay before file ops
    time.sleep_ms(50)

    # Initialize log files
    for fname in file_list:
        with open(fname, 'w') as f:
            if 'house' in fname:
                f.write("Timestamp, ms5611 Temperature (C), Pressure (mbar), TempE (deg), TempI (deg), Lat (deg), Lon (deg), Alt (m), HDOP \n")
            elif 'data_log' in fname:
                f.write("MLX90640 Raw Data Values \n")
            elif 'trigger' in fname:
                f.write("Timestamp, Trigger, Condition, Pressure (mbar), Alt (m) \n")
            else:
                f.write("Timestamp, Error, Sensor/Class \n")           # recording of errors by time and what class raised it

    print(f" Files created at time {time.time()}")
except Exception as e:
    print("Files not initialised", e)

# MORE SETUP: initializing sensors

# Pressure Sensor
try:
    pressure_sensor = MS5611(i2c_bus=0, sda_pin=4, scl_pin=5, address = 0x77)
except Exception as e:
    pressure_sensor = None
    print("Pressure Sensor Error")
    
    #writing error to error log
    with open(file_list[2], "a") as file:
        file.write(f"{time.time()}, {e}, Pressure Sensor \n") 

# Temperature Sensor(s)
try:
    temp_sensor = DS18B20(pin=21)

if not temp_sensor.available:
    print("Temperature Sensor Error")
    temp_sensor = None
    
    #writing error to error log
    with open(file_list[2], "a") as file:
        file.write(f"{time.time()}, Temp Sensor not Available, Temp Sensor \n") 


# Thermal Sensor
try:
    frame_taker = MLX90640(i2c=0, address=0x33, sda_pin=4, scl_pin=5)
    frame_taker.refresh_rate = RefreshRate.REFRESH_8_HZ                 # currently the fasted refresh rate that doesn't kill itself,
                                                                        # reason unclear and seen by many users of the product online
except Exception as e:
    frame_taker = None
    print("MLX90640 Sensor Error")
    
    # writing error to error log
    with open(file_list[2], "a") as file:
        file.write(f"{time.time()}, {e}, Thermal Sensor \n")
    

# GPS 
try:
    gps_sensor = SQTGPS(uart_bus = 1, baudrate = 9600, tx_pin = 8, rx_pin = 9)
except exception as e:
    gps_sensor = None
    print("GPS Sensor Error")
    
    #writing error to error log
    with open(file_list[2], "a") as file:
        file.write(f"{time.time()}, {e}, GPS \n")

# Communications
try:
    TTT = Comms(file_list, address = 0x53, callsign = "SQRT", uart_bus=0, tx_pin = 0, rx_pin = 1)

except Exception as e:
    TTT = None
    print(f"T-cubed Error: {e}")
    
    
    #writing error to error log
    with open(file_list[2], "a") as file:
        file.write(f"{time.time()}, {e}, TTT \n")
    

#initializing servo:
try:
    servo_motor = Servo()
except Exception as e:
    print("Servo initialization error")
    
    #writing error to error log
    with open(file_list[2], "a") as file:
        file.write(f"{time.time()}, {e}, Servo \n")
    
    
#initializing triggering class, should just always happen since there's no sensor to connect with:
triggering = SQTtrigger()

# LAST SETUP: setting all the flags and counters

trigger = False       # flag to trigger valve
trigger_condition = None      # to set trigger condition too so we know what message to send
counter = 1     # for timing transmitions
error_counter = 0
frame_count = 0

#defining initiating float array for thermal sensor
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
        pressure_T, pressure_P = pressure_sensor.log_pressure()
        t = time.time()


        try:
            time.sleep_ms(1000)
            #with open(file_list[0], "a") as f:         #writing the first part of the housekeeping data line
                #if pressure_T == None or pressure_P == None:
                    #f.write(f"{t}, NaN, NaN, ")
                #else:
                    #f.write(f"{t}, {T}, {P}, ")
        
        except Exception as e:
            #print("the end: ,", e)
                
            #writing error to error log
            
            with open(file_list[2], "a") as file:
                file.write(f"{time.time()}, {e}, Pressure Sensor \n")
        
    #2. temperature sensors (internal and external)

    if temp_sensor:
        try:
            #temp_sensor.log_temp(file_list[0])
            tempE, tempI = temp_sensor.read_temp(file_list[2])  # recently swaped tempE and tempI cuz I think I had them backwards
            
        except Exception as e:
            print("Temperature not logged", e)
            
            #writing error to error log
            with open(file_list[2], "a") as file:
                file.write(f"{time.time()}, {e}, Temp Sensors \n")
        

    time.sleep_ms(100)
        


    #3. GPS

    if gps_sensor:
        try:
            gps_data = gps_sensor.gps_log()
    
            #if gps_data: 
                
                #with open(file_list[0], 'a') as file:
                #    file.write(f"{gps_data[1]}, {gps_data[2]}, {gps_data[3]}, {gps_data[4]} \n")
            #else:
                #with open(file_list[0], 'a') as file:
                #    file.write("NaN, NaN, NaN, NaN \n")
        except Exception as e:
            print("GPS not logged:", e)
            
                #writing error to error log
            with open(file_list[2], "a") as file:
                file.write(f"{time.time()}, {e}, GPS \n")

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
        gps_data = [time.time(), 'None', 'None', 'None', 99.99]
    elif len(gps_data) != 5:
        diff = 5 - len(gps_data)
        
        for i in diff:
            gps_data.append(99.99)
        
    #writing to file:
    # Keys: Timestamp, ms5611 Temperature (C), Pressure (mbar), TempE (deg), TempI (deg), Lat (deg), Lon (deg), Alt (m), HDOP 
    house_list = [time.time(), pressure_T, pressure_P, tempE, tempI, gps_data[0], gps_data[1], gps_data[2], gps_data[3], gps_data[4]]
    
    try:
        with open(file_list[0], "a") as file:
            file.write(f"{time.time()}, {pressure_T}, {pressure_P}, {tempE}, {tempI}, {gps_data[1]}, {gps_data[2]}, {gps_data[3]}, {gps_data[4]} \n") 
    except Exception as e:
        with open(file_list[2], "a") as file:
            file.write(f"{time.time()}, {e}, Writing Housekeeping to SD \n")

    #5. TRIGGER CHECK (only happends when trigger = False). if true, servo imediately activated.
                
    #interlude: make science frame array each time in the loop. make one here right before it may be needed. 
    science_frame = init_float_array(768)
    
    if not trigger:
        p_dict, gps_dict = triggering._parse_files_triggering(file_list[0])

        trigger, condition, pres, alt = triggering.trigger_check(p_dict, gps_dict)
        
        t = time.time()
        with open(file_list[3], "a") as f:
            f.write(f"{t}, {trigger}, {condition}, {pres}, {alt} \n")
        
        if trigger:
            try:
                servo_motor.run_servo()
            except Exception as e:
                print(f"servo motor connection exception: {e}")
                
                #writing error to error log
                with open(file_list[2], "a") as file:
                    file.write(f"{time.time()}, {e} during triggering, Servo \n")
            
            #try:
                # i2c.freq(240000000)
                
            
            
            science_data = []
            science_times = []
            for i in range(16):
                # getting 8 science frames in a row right after the servo triggers (we actualyl want to get 30 :/ )
                try:
                    science_frame = init_float_array(768)
                
                    frame_taker.get_frame(science_frame)
                except Exception as e:
                    print(f"frame taker exception: {e}")
                                    #writing error to error log
                    with open(file_list[2], "a") as file:
                        file.write(f"{time.time()}, {e}, Thermal Sensor \n")
        
                    science_frame = [0]
                
                t = time.time()
                
                science_times.append(t)
                science_data.append(science_frame)
            with open(file_list[4], "a") as f:
                for i, line in enumerate(science_data):
                    f.write(f"Time: {science_times[i]} \n")
                    for temp in line:
                        f.write(f"{temp},")
                    f.write("\n")
            
            


    #6. Thermal Sensor
    def init_float_array(size) -> array.array:
        return array.array('f', (0 for _ in range(size)))

    if frame_taker:
        # Two frames are taken to get a value for each pixel.
        for _ in range(2):
            frame = init_float_array(768)
            frame_taker.get_frame(frame)
            t = time.time()
    
            with open(file_list[1], "a") as f:
                f.write(f"{t} FRAME DATA: \n")
                for temp in frame:
                    f.write(f"{temp},")
                f.write("\n")      

         #   print("Thermal Array not logged", e)

    time.sleep_ms(100)       
        


    #7. Data downlinks: check counter for timing of science and telem packet sending
    
    if trigger:
        trig_status = True
    
    trigger = False
    if TTT:
        if counter % 7 == 0: 
            print("Sending science packet")
            TTT.science_packet(trig_status, condition, pres, alt, frame, frame_count)
                
        if counter % 5 == 0:
            print("Sending telemetry packet")

            error_counter = TTT.telem_packet(error_counter)
            
            print(f"what EC is set to: {error_counter}")

        
    print(f'########LOOP COUNTER {counter} ###################')
    counter += 1
    
    if trigger:
        frame_count += 1
    time.sleep(1)

