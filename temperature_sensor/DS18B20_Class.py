class DS18B20:
    """Interface to the DS18B20 thermometer"""

    def __init__(self, address: ds18x20.DS18X20(onewire.OneWire(one_wire_pin))) -> None:



    def detect_device(self, Pin=17):
        """
        This function detects a one-wire device at the input pin specified.

        Inputs:
        Pin Number - GPIO number on Pico used (will be defined in mission main function.
        """
    
        one_wire_pin = machine . Pin (17)

        # The temperature sensor addresses are identified and the found
        # devices are named. 
        temperature_sensors = ds18x20.DS18X20(onewire.OneWire(one_wire_pin))
        roms = temperature_sensors.scan()

    def read_temp(self, ):
        """
        Reads the temperature from the sensor
        """
        
        # The temperature sensor is asked to make a measurement.
        temperature_sensors.convert_temp()
        
        # The sensor is given time to make the measurement before the data is requested.
        time.sleep_ms(750)
        tempC = temperature_sensors.read_temp(roms[0])


    def file_temp(self, filename = "thermo_readings.txt"):
        """
        Stores temperature values in a suitably parsed, formatted textfile.

        Inputs:
        filename (str) - Name of textfile
        """

        with open(filename, "a") as f:
            
                  
        











    def 





