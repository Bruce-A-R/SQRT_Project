"""
ds18b20.py

Authors: Caimin Keavney, Bruce Ritter
Version Date: 30/3/2026

This class is used to initialize and read data from the temperature sensor.
"""


import machine, time, onewire, ds18x20

class DS18B20:
    """Interface to the DS18B20 thermometer"""

    def __init__(self, pin=17):
        """
        Initialises the sensor.

        pin (int): GPIO pin used for the one-wire bus
        
        There should be two temperature sensors attached with the same OneWire connection,
        where are found with roms[0] and roms[1]
        """
        self.pin = machine.Pin(pin)
        self.onewire = onewire.OneWire(self.pin)
        self.sensor = ds18x20.DS18X20(self.onewire)
        self.roms = self.sensor.scan()
        self.available = len(self.roms) >= 1
        self.rom_E = self.roms[0] if len(self.roms) >= 1 else None
        self.rom_I = self.roms[1] if len(self.roms) >= 2 else None



    def read_temp(self, error_log):
        """
        Reads the temperature from the sensor
        Returns None if sensor unavailable,
        and writes the error to inputted error log if there is an error raised.
        
        Input: path to error log file
        Output: temperatures read from sensors (float if read, None if theres a reading error)
        """
        # Check to see if device is at address.
        if not self.available:
            return None, None

        try:
            # The temperature sensor is asked to make a measurement.
            self.sensor.convert_temp()
        
        
        except Exception as e:
            
            with open(error_log, "a") as file:
                file.write(f"{time.time()}, {e}, Temp Sensor Converting Temp")

            
            
            # The sensor is given time to make the measurement before the data is requested.
            time.sleep_ms(150)
        try:
            tempE = self.sensor.read_temp(self.rom_E) if self.rom_E else None
            
        except Exception as e:
            print(f"Exception reading temperature: {e}")
            
            #writing error if it happens:
            with open(error_log, "a") as file:
                file.write(f"{time.time()}, {e}, Temp Sensor \n")
            
            tempE = None
        
        try:
            tempI = self.sensor.read_temp(self.rom_I) if self.rom_I else None
            
        except Exception as e:
            print(f"Exception reading temperature: {e}")
            
            #writing error if it happens:
            with open(error_log, "a") as file:
                file.write(f"{time.time()}, {e}, Temp Sensor \n")
            
            tempI = None
            
        return tempI, tempE

                
        
