class MS5611:
    """Interfaces with the Pressure/Temperature Sensor"""

    def ___init___(self, i2c_bus:machine.I2C):
        






    def unpack(buffer):
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
    return sum(_byte << (_i * 8) for _i , _byte in enumerate (_buffer ))



    def read_calibration_const(bus, address):
    """
    Reads in the calibration constants from the onboard memory.
    
    Inputs:
    bus (I2C Object) - name of the bus where memory is stored e.g. i2c
    address (int) - Address of the measuring device.
    
    Returns:
    calib (list) - 6 calibration constants.
    """
    # The list of calibration constants is initiated with a null value
    # to simplify indexing for calibration calculations later.
    calib = [None]

    # The registry addresses are cycled through to retrieve the 6 calibration constants
    for i in range(1, 7):
        # This incrementing process is needed to cover all the relevant registers.
        regis = 0xA0 + i*2

        # The raw 16 bit unsigned integer describing the calibration constant is read in.
        try:
            raw = bus.readfrom_mem(address, regis , 2)

        except Exception as e:
            raise RuntimeError(f"I2C read failure:", {e})
            
        # If the constant is there, it is unpacked and stored.
        if len(raw) != 2:
            raise RuntimeError("Invalid calibration read")
           
        else:
            calib.append(unpack(raw))
        
    return calib


    def read_adc(bus, address, cmd):
    """
    Reads in the pressure or temperature adc value depending on the user's preference.

    Inputs:
    bus (I2C object): name of the bus where the memory is stored e.g. i2c
    address (int): name of the device to be requested from
    cmd (str): 'T' for temperature or 'P' for pressure

    Returns:
    adc (int) - Pressure or Temperature ADC value.
    """
    # The conversion command is chosen.
    if cmd == 'T':
        command = TEMPERATURE_ADC
    elif cmd == 'P':
        command = PRESSURE_ADC

    else: 
        raise ValueError("cmd must be 'T' or 'P'")

    # The command is sent.  
    try:
        bus.writeto(address, command)

    except Exception as e:
        raise RuntimeError("I2C write failed:",e)

    time.sleep_ms(20)

    # Read ADC result from the register after short wait.
    try:
        adc_bytes = bus.readfrom_mem(address, 0x00, 3)

    except Exception as e:
        raise RuntimeError("I2C read failed:", e)

    # Check that valid ADC value was read in from memory.
    if len(adc_bytes) != 3:
        raise RuntimeError("Invalid ADC value length")

    adc = unpack(adc_bytes)
    
    return adc






    def compute_pressure(T_val, P_val, calib_const):
    """
    Uses calibration constants to compute and return calibrated pressure and temperature values.
    The calibration process is guided by the MS5611 datasheet (pages 7-8).
    Inputs:
    T_val, P_val (int) - Raw adc values (temperature and pressure) returned by read_adc function.
    calib_const(list) - 6 calibration constants returned by read_calibration_constants function.

    Returns:
    TEMP (float) - calibrated temperature value in centicelsius 
    P (float) - calibrated pressure value in centimillibars
    """
    # The calibration constants list is assigned to an easier name for indexing.
    c = calib_const

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
            OFF2 = OFF2 + 7*(TEMP+1500)**2
            SENS2 = SENS2+11*(TEMP+1500)**2/2
    # High temperature
    else:
        T2 = 0
        OFF2 = 0
        SENS2 = 0


    # Calculate compensated Pressure and Temperature values
    TEMP = TEMP - T2
    OFF = OFF-OFF2
    SENS = SENS - SENS2

    P = (P_val*SENS/(2**21) - OFF)/(2**15)
    

    return TEMP, P




    def read_pressure(bus,addr, calibs):
    """
    Returns calibrated, formatted pressure and temperature figures with units.

    Inputs:
    bus (I2C object) - name of the bus where data is stored
    addr (int) - address of the MS5611 pressure sensor
    calibs (list) - Calibration constants returned by read_calibration_constants

    Returns:
    T_C (float) - Calibrated Temperature (in C)
    P_mb (float) - Calibrated Pressure (in mb)
    
    """
    # The adc values for pressure and temperature are read in.
    T_val = read_adc(bus, addr, 'T')
    P_val = read_adc(bus, addr, 'P')

    # The calibrated temperature and pressure values are returned by the compute_pressure function.
    T, P = compute_pressure(T_val, P_val, calibs)

    # In this version, the values will be left as integers (no conversion).
    
    return T, P



    
