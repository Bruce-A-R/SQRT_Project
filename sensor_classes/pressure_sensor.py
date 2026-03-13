"""
Class for interacting with the MS5611 sensor for retrieval of external pressures/temperatures
"""
# Necessary imports made.
import machine, time

class MS5611:
    """Interfaces with the Pressure/Temperature Sensor"""

    def __init__(self, i2c_bus, sda_pin, scl_pin, address = 0x77):
        """
        Initialises the sensor
        """
        self.i2c = machine.I2C(
            i2c_bus, 
            scl=machine.Pin(scl_pin), 
            sda = machine.Pin(sda_pin))
        
        print(self.i2c)
        
        
        self.devices = self.i2c.scan()
        print(self.devices)
        
        
        self.address = address
    

        self.available = True
        
        
        if self.address not in self.devices:
            self.available = False
            self.calib = None
        
        time.sleep_ms(50)
        if self.available:
            try:
                self.calib = self.read_calibration_const()
            except OSError:
                print("PROM read failed")
                self.calib = None
                
            
        






    def unpack(self, buffer):
        """ Unpacks MSB - ordered buffer of bytes into an unsigned integer .
        Note : buffer must be a bytes - like object or a list of integers in the
        range [0 , 255].
        Usage :
        >>> unpack ([0x01 , 0x00 ])
        256
        >>> unpack ([0x10 , 0x00 ])
        4096
        >>> unpack ([0xFF , 0xFF , 0xFF ])
        16777215
        """
        _buffer = reversed(bytearray(buffer))
        return sum(_byte << (_i * 8) for _i , _byte in enumerate(_buffer ))



    def read_calibration_const(self):
        """
        Reads in the calibration constants from the onboard memory.
        
        Returns:
        calib (list) - 1 None, 6 calibration constants (for indexing in compute_pressure)
        """
        # The list of calibration constants is initiated with a null value
        # to simplify indexing for calibration calculations later.
        calib = [None]
        
        
        # The registry addresses are cycled through to retrieve the 6 calibration constants
        for i in range(1, 7):
            # This incrementing process is needed to cover all the relevant registers.
            reg = 0xA0 + i*2
        
            # The raw 16 bit unsigned integer describing the calibration constant is read in.
            raw = self.i2c.readfrom_mem(self.address, reg , 2)
                

            # Calibration constants are stored.
            calib.append(self.unpack(raw))
        
        print(calib)
        return calib


    def read_adc(self, cmd):
        """
        Reads in the pressure or temperature adc value depending on the user's preference.
    
        Inputs:
        cmd (str): 'T' for temperature or 'P' for pressure
    
        Returns:
        adc (int) - Pressure or Temperature ADC value.
        """
        # Checks done to ensure device is available at address
        if not self.available:
            return None

        # The conversion command is chosen.
        if cmd == 'T':
            command = b'\x58'
        elif cmd == 'P':
            command = b'\x48'
    
        else: 
            return None
    
        # The command is sent.
        self.i2c.writeto(self.address, command)

        # Sensor given time to collect adc values
        time.sleep_ms(20)
    
        # Read ADC result from the register after short wait.
        try:
            adc_bytes = self.i2c.readfrom_mem(self.address, 0x00, 3)
        except:
            print("ADC fail")

        # Raw data unpacked and returned.
        adc = self.unpack(adc_bytes)
        
   
        return adc






    def compute_pressure(self, T_val, P_val):
        """
        Uses calibration constants to compute and return calibrated pressure and temperature values.
        The calibration process is guided by the MS5611 datasheet (pages 7-8).
        Inputs:
        T_val, P_val (int) - Raw adc values (temperature and pressure) returned by read_adc function.
    
        Returns:
        TEMP (float) - calibrated temperature value in celsius 
        P (float) - calibrated pressure value in millibars
        """
        # The calibration constants list is assigned to an easier name for indexing.
        c = self.calib
    
        # FIRST ORDER
        # Calculating Temperature (in centicelsius)
        dT = T_val - c[5]*(2**8)
        TEMP = 2000 + (dT*c[6])/(2**23)
        # Calculating offset and sensitivity.
        OFF = c[2]*(2**16) + (c[4]*dT)/(2**7)
        SENS = c[1]*(2**15) + (c[3]*dT)/(2**8)
    
        # SECOND ORDER TEMPERATURE COMPENSATION
        # Low temperature
        if TEMP < 2000:
            T2 = (dT**2)/(2**31)
            OFF2 = 5*((TEMP-2000)**2)/2
            SENS2 = 5*((TEMP-2000)**2)/(2**2)
    
            # Very low temperature
            if TEMP<-1500:
               OFF2 = OFF2 + 7*((TEMP+1500)**2)
               SENS2 = SENS2 + 11*(((TEMP+1500)**2)/2)
        # High temperature
        else:
            T2 = 0
            OFF2 = 0
            SENS2 = 0
    
    
        # Calculate compensated Pressure and Temperature values
        TEMP = TEMP - T2
        OFF = OFF-OFF2
        SENS = SENS - SENS2
    
        P = ((P_val*SENS)/(2**21) - OFF)/(2**15)
        
    
        return TEMP/100, P/100
    



    def log_pressure(self, filename):
        """
        Writes calibrated, formatted pressure and temperature figures to a textfile.
    
        Inputs:
        filename (str) - Name of textfile for data storage
        """
        if not self.available:
            T_val, P_val = None, None
        
        
        # The adc values for pressure and temperature are read in.
        T_val = self.read_adc('T')
        P_val = self.read_adc('P')

        if T_val is None or P_val is None:
            t = time.time()

            try:
                with open(filename, "a") as f:
                    f.write(f"{t}, NaN, NaN\n")
            except Exception as e: 
                print("File writing exceoption for NaN values case:", e)
                print("t, T, P: {t}, NaN, NaN")
                
        else:
            # The calibrated temperature and pressure values are returned by the compute_pressure function.
            T, P = self.compute_pressure(T_val, P_val)
            print(T,P)
            t = time.time()
            
            time.sleep_ms(100)
            # T (celsius) and P (millibars)
            with open(filename, "a") as f:
                try:
                    f.write(f"{t}, {T}, {P}\n")
                except Exception as e:
                    print("File writing exception for T, P case:", e)
                    print(f"t, T, P: {t}, {T}, {P}")
        


        


            
                  


    

