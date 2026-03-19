"""
This class is for the temperature sensor to be used for internal temperature readings/valve 
operation verification.
"""
# All necessary imports are performed.
import machine, time, onewire, ds18x20

class DS18B20:
    """Interface to the DS18B20 thermometer"""

    def __init__(self, pin=21):
        """
        Initialises the sensor.

        pin (int): GPIO pin used for the one-wire bus
        """
        self.pin = machine.Pin(pin)
        self.onewire = onewire.OneWire(self.pin)
        self.sensor = ds18x20.DS18X20(self.onewire)
        self.roms = self.sensor.scan()
        print(self.roms)
        self.available = len(self.roms) >= 1
        self.rom_E = self.roms[0] if len(self.roms) >= 1 else None
        self.rom_I = self.roms[1] if len(self.roms) >= 2 else None



    def read_temp(self):
        """
        Reads the temperature from the sensor
        Returns None if sensor unavailable.
        """
        # Check to see if device is at address.
        if not self.available:
            return 99.99, 99.99

        try:
            # The temperature sensor is asked to make a measurement.
            self.sensor.convert_temp()

            
            # The sensor is given time to make the measurement before the data is requested.
            time.sleep_ms(150)
            
            tempE = self.sensor.read_temp(self.rom_E) if self.rom_E else 99.99
            tempI = self.sensor.read_temp(self.rom_I) if self.rom_I else 99.99

            return tempE, tempI
            
        except Exception as e:
            return 99.99, 99.99



                
        


            
                  
        
