from ms5611 import MS5611
from ds18b20 import DS18B20
from mlx90640 import MLX90640

import time
import machine

try:
    pressure_sensor = MS5611(i2c_bus=1, sda_pin=6, scl_pin=7)
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
    print("MLX90640 Failure")

print(pressure_sensor.i2c.scan())
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
