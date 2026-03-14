"""
This class is for the temperature sensor to be used for internal temperature readings/valve 
operation verification.
"""
# All necessary imports are performed.
import machine, time, onewire, ds18x20


class DS18B20:
    """Interface to the DS18B20 thermometer"""

    def __init__(self, pin=22):
        """
        Initialises the sensor.

        pin (int): GPIO pin used for the one-wire bus
        """
        self.pin = machine.Pin(pin)
        self.onewire = onewire.OneWire(self.pin)
        self.sensor = ds18x20.DS18X20(self.onewire)

        # Scan for devices at address defined above.
        self.roms = self.sensor.scan()



        if not self.roms:
            self.available = False
        else:
            self.available = True




    def read_temps(self):
        """
        Reads the temperature from the sensor
        Returns None if sensor unavailable.
        """
        # Check to see if device is at address.
        if not self.available:
            return None

        try:
            # The temperature sensor is asked to make a measurement.
            self.sensor.convert_temp()
            
            # The sensor is given time to make the measurement before the data is requested.
            time.sleep_ms(300)
            
            temps = []
            for rom in self.roms:
                temps.append(self.sensor.read_temp(rom))

            return temps
            
        except Exception as e:
            print("Temp read error:", e)
            return None

    def log_temp(self, filename):
        """
        Reads temperature and appends it to a file.
        """
        temps = self.read_temps()
        
        timestamp = time.time()
        
        with open(filename, "a") as f:
            if temp is None:
                f.write(f"{timestamp}, NaN\n")

            else:
                try:
                    f.write(f"{timestamp}, {temp}\n")
                except Exception as e:
                    print("error", e)
        


            
                  


    

