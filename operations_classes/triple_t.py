"""
triple_t.py

The code below will be used to collect relevant data, format telemetry/science data packets, and
interface with communications architecture.

Functions:
get_last_entry
parse_time
cropping
telem_packet
science_packet
"""


from ucollections import namedtuple
import os
import machine
import time
from _rhserial_radio import RHSerialRadio
from _tuppersat_radio import TupperSatRadio as SatRadio


class Comms:
  def __init__(self, files, address = 0x53, callsign = 'SQRT',uart_bus = 0, tx_pin = 0, rx_pin = 1):
      self.radio_settings = {
                       'address' : address,
                        'callsign' : callsign
                            }
      self.uart = machine.UART(uart_bus, baudrate = 38400, tx = machine.Pin(tx_pin), rx = machine.Pin(rx_pin))
    
      self.radio = SatRadio(self.uart, **self.radio_settings)

      # Counts initialised for determining packet numbers.
      self.t_packet_count = 0
      self.d_packet_count = 0

      # SD card file paths defined for data gathering.
      self.sd_files = {
      "Housekeeping": files[0],
        "MLX": files[1],
        "Error" :files[2],
          "Trigger": files[3],
          "MLX_Science": files[4]
        }

        
  def get_last_entry(self, filepath):
      """
      Reads the last line from a text file on the SD card.

      Inputs:
      filepath (str) - Filepath containing the relevant data.

      Returns:
      last_line (str) - The most recently appended line to the textfile.
      """
      try:
          with open(filepath, 'r') as f:
              lines = f.readlines()
          if len(lines)>1:
              line = lines[-1]
           
      except:
          line = None

      return line

  

  Time = namedtuple('Time', 'hour minute second microsecond')

  def chunk(self, string, n):
    """Break a string into chunks of length n."""
    return (string[i:i+n] for i in range(0, len(string), n))


  def parse_time(self, time_str):
    """Parse a time string HHMMSS.SSS into a Time object."""
    if time_str == None:
        return None
    elif time_str == "None":
        return None
    else:
        # split out the second and sub-second times
        _hhmmss, _milliseconds = time_str.split('.')

        # compute the sub-second time in microseconds
        _us = int(_milliseconds) * 1000

        # compute the hours, minutes and seconds
        _hh, _mm, _ss = (int(x) for x in self.chunk(_hhmmss, 2))

        return self.Time(_hh, _mm, _ss, _us)

    
  def telem_packet(self, hk_parts, error_count):
    """
    Telemetry packet is formatted and sent.
    """
    
    # MS5611
    
    try:
        P = hk_parts[2]
    except:
        P = 9999.9999
        
    # DS18B20 Sensors
    try:
        TE, TI= hk_parts[3], hk_parts[4]
    
    except:
        TE, TI = 999.999, 999.999
        
    # GPS 
    try:
        gps_time, lat, lon, alt, hdop = hk_parts[5:10]
    
    except:
        gps_time, lat, lon, alt, hdop = None, 00.00000, 000.00000, 00000.00, 00.00
      
    
    # Still reading in from SD card for error reports.
    # Will not work if SD card not working (An Error Report in itself really)
    #try:
    with open(self.sd_files["Error"], "r") as f:
        try:
            error_lines = f.readlines()
            error_counter_new = len(error_lines)   # Error Count is updated
          
        except:
            error_counter_new = error_count
    try:
        error_parts = self.get_last_entry(self.sd_files["Error"]).split(',') 
    except:
        error_parts = None
    
    if error_counter_new != error_count: 
        try:
            error = error_parts[-1]    # Error type is defined.
        except:
            error = "None"
            
    else:
        error = "None"
            
    
    
    
     
    gps_time = self.parse_time(gps_time)
    
    print(error_counter_new)
    print(error)
    telem_dict = {
      'hhmmss' : gps_time,              # time from GPS, is sometimes None but that should be handled
      'latitude': lat,           		# Latitude in metres
      'longitude' :lon,      			# Longitude in degrees
      'altitude':alt,                   # Altitude in metres
      'hdop': hdop,                     # HDOP
      't_internal' : TI,       			# Internal temperature in Celsius
      't_external': TE,        			# External temperature in Celsius
      'pressure': P,					# External Pressure in millibars
      'error_count': error_counter_new, # Error Count
      'error_type': error               # Error Type
      
      
    }
    print(telem_dict)
    # The formatted data packet is transmitted
    self.radio.send_telemetry(**telem_dict)
    
    # New Error Count is returned for next iteration
    return error_counter_new

  def cropping(self, frame, crop_w=8, crop_h=6):
    """
    Function to crop thermal array returned by MLX90640 to a 8x6 array

    Inputs:
    frame (list) - array of 768 temperature values to be cropped

    Returns:
    cropped_frame (list) - combined frame of 48 temperature values in the region of interest.
    """
    
    width, height = 32, 24
    start_x = (width - crop_w) // 2
    start_y = (height - crop_h) // 2

    full_cropped_frame = []
    for y in range(start_y, start_y + crop_h):
        for x in range(start_x, start_x + crop_w):
            index = y * width + x
            # Sum the corresponding values from both frames
            full_cropped_frame.append(frame[index])

    return full_cropped_frame

  
  def science_packet(self,trigger, trig_type, pres, alt, frame):
    """
    Science packet is formatted and sent.
    
    Inputs:
    trigger (bool): Whether or not the trigger condition has been satisfied
    trig_type (str): Subsystem causing most recent error
    pres (float): Pressure used to determine trigger status
    alt (float): Altitude used to determine trigger status
    frame (array): Array of temperatures from MLX90640
    frame_count (int): The science frame to be transmitted if the trigger condition has been met.
    """

    
    # Most recent thermal array is loaded in from the SD card and cropped for ease of transmission
    try:
        # Frame is cropped for transmission
        crop_frame = self.cropping(frame)
    
    except:
        crop_frame = None

    print(crop_frame)
    # Data dictionary is formatted.
    data_dict = {
      'data' : crop_frame,                # 48 temperature values (Celsius)               
      'trig_status' : trigger,                      # Trigger Flag (Bool Type)
      'trig_type' : trig_type,				# Trigger Type (Character "G", "B", "U")
      'pressure': pres,                    # Pressure (millibars)
      'altitude':alt                      # Altitude (metres)

      }
    # Packet is transmitted 

    self.radio.send_data(**data_dict)


    
    
    
    





    
    
    
    





    
    
    
    


