"""
The code below will be used to collect relevant data, format telemetry/science data packets, and
interface with communications architecture.
"""

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

  def get_line(self,filepath, index):
      """Reads entered line from a text file on the SD card.
      
      Inputs:
      filepath (str) - Name of filepath as on SD card
      index (int) - Desired line of file
      
      Returns:
      line (str) - Requested line from file in string format
      """
      
      try:
          with open(filepath, 'r') as f:
              lines = f.readlines()
                
              length = len(lines)
              
              index = index%length
              
              line = lines[index]
      except:
          line = None
          
      return line
    
  def telem_packet(self, error_count):
    """
    Telemetry packet is formatted and sent.
    """
    # The telemetry data is collected from the corresponding files on the SD card.
    hk_parts = self.get_last_entry(self.sd_files["Housekeeping"]).split(',')
    print(hk_parts)

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
        lat, lon, alt, hdop = hk_parts[5:9]
        
    
    except:
        lat, lon, alt, hdop = 00.00000, 000.00000, 00000.00, 00.00
      
    
    try:
        with open(sd_files["Error"], "r") as f:
            error_lines = f.readlines()
            error_counter_new = len(error_lines)
          
    except:
        error_counter_new = error_count
    try:
        error_parts = self.get_last_entry(self.sd_files["Error"]).split(',')
    except:
        error_parts = None
    
    if error_counter_new != error_count: 
        try:
            error = error_parts[2]
        except:
            error = "None"
            
    else:
        error = "None"
            
        
    #try:
        #with open(self.sd_files["Trigger"], "r") as file:
       #     lines = file.readlines()
      #      trig_data = lines[-1]
     #       condition = True
    
    #except:
      #  condition = False

    telem_dict = {
      'hhmmss' : time.localtime(),
      'latitude': lat,           		# Latitude in metres
      'longitude' :lon,      			# Longitude in degrees
      'altitude':alt,
      'hdop': hdop,                     # Altitude in metres
      't_internal' : TI,       			# Internal temperature in Celsius
      't_external': TE,        			# External temperature in Celsius
      'pressure': P,					# External Pressure in millibars
      'error_count': error_counter_new,
      'error_type': error
      
      
    }

    # The formatted data packet is transmitted
    
    self.radio.send_telemetry(**telem_dict)
    
    return error_counter_new

  def cropping(self, frame, crop_w=8, crop_h=6):
    """
    Function to crop thermal array returned by MLX90640 to a 8x6 array

    Inputs:
    frame (list) - 768 temperature values to be cropped

    Returns:
    cropped_frame (list) - 48 temperature values in the region of interest.
    """
    # Size of the initial frame is defined.
    width = 32
    height =24

    # The first array element to be appended to the cropped frame is determined
    # Assumed to be in the centre of the frame (will be changed after testing).
    start_x = (width-crop_w)//2
    start_y = (height-crop_h)//2

    cropped_frame = []

    # Cropped frame is populated with appropriate temperature values from the ROI.
    for y in range(start_y, start_y + crop_h):
      for x in range(start_x, start_x +crop_w):
        index = y*width + x
        cropped_frame.append(frame[index])

    return cropped_frame


  
  def science_packet(self, trigger, frame_count):
    """
    Science packet is formatted and sent.
    
    Inputs:
    trigger (bool): Whether or not the trigger condition has been satisfied
    frame_count (int): The science frame to be transmitted if the trigger condition has been met.
    """

    
    # Most recent thermal array is loaded in from the SD card and cropped for ease of transmission
    try:
        if not trigger:
            raw = self.get_last_entry(self.sd_files["MLX"])
        else:
            raw = self.get_line(self.sd_files["MLX_Science"], frame_count)

        clean = raw.strip()[1:-1]  # removes the starting '[' and ending ']'

        items = clean.split(',')

        frame = [float(val.strip().replace("'", "")) for val in items]
        
        crop_frame = self.cropping(frame)

    except:
        crop_frame = None

    
    try:
        trig, trig_type, pres, alt= self.get_last_entry(self.sd_files["Trigger"]).split(',')[1:]
    except:
        trig, trig_type, pres, alt = None, None, None, None

    # Data dictionary is formatted.
    data_dict = {
      'data' : crop_frame,                # 48 temperature values (Celsius)               
      'trig_status' : trig,                      # Trigger Flag (Bool Type)
      'trig_type' : trig_type,				# Trigger Type (Character "G", "B", "U")
      'pressure': pres,
      'altitude':alt

      }
    
    # Packet is transmitted 

    self.radio.send_data(**data_dict)


    
    
    
    


