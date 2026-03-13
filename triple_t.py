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
  def __init__(self, address = 0x53, callsign = 'SQT',uart_bus = 0, tx_pin = 0, rx_pin = 1):
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
        "External_TP": "/sd/external_readings.txt",
        "Internal_T": "/sd/thermo_readings.txt",
        "GPS": "/sd/gps_log.txt",
        "MLX": "/sd/mlx_readings.txt",
        "Servo": "/sd/servo_status.txt",
        "Trigger": "/sd/trig_log.txt",
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
     with open(filepath, 'rb') as f:
       # The end of the file is located.
       f.seek(0, os.SEEK_END)
       position = f.tell() - 1
 
       # Keeps moving backwards until a newline is found.
       while position>0:
         f.seek(position)
         if f.read(1) == b'\n':
           break
         position -= 1
       last_line = f.readline().decode()
     return last_line.strip()
    except OSError:
     return ""
    
  def telem_packet(self):
    """
    Telemetry packet is formatted and sent.
    """
    # Packet Type is specified
    packet_type = 'T'

    # The telemetry data is collected from the corresponding files on the SD card.
    try:
        lat,lon,alt = self.get_last_entry(self.sd_files["GPS"]).split(',')[1:]
    except:
        lat,lon,alt = None, None, None
    try:
        TE, P = self.get_last_entry(self.sd_files["External_TP"]).split(',')[1:]
    except:
        TE, P = None, None
        
    try:
        TI = self.get_last_entry(self.sd_files["Internal_T"]).split(',')[1]
    except:
        TI = None

    telem_dict = {
      'hhmmss' : time.localtime(),
      'latitude': 53.12345,#lat,           		# Latitude in metres
      'longitude' : 123.4567,#lon,      			# Longitude in degrees
      'altitude' : 50.0,#alt,                 # Altitude in metres
      't_internal' : 45.7689,#TI,       			# Internal temperature in Celsius
      't_external': 332.594,#TE,        			# External temperature in Celsius
      'pressure':1102.4549,# P,        			# External Pressure in millibars
      
    }

    # The formatted data packet is transmitted
    
    self.radio.send_telemetry(**telem_dict)
    


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


  
  def science_packet(self):
    """
    Science packet is formatted and sent.
    """

    # Most recent thermal array is loaded in from the SD card and cropped for ease of transmission
    try:
        frame = [float(x) for x in self.get_last_entry(self.sd_files["MLX"]).split(',')]
        crop_frame = self.cropping(frame)
    except:
        crop_frame = None

    # The current flag statuses are read in.
    try:
        servo_motor = int(self.get_last_entry(self.sd_files["Servo"]))
    except:
        servo_motor = None
    try:
        trig, trig_type= self.get_last_entry(self.sd_files["Trigger"]).split(',')[1:]
    except:
        trig, trig_type = None, None

    # Data dictionary is formatted.
    data_dict = {
      'data' : crop_frame,                # 48 temperature values (Celsius)
      'servo_flag' : servo_motor,                # Servo Motor flag (Bool Type)
      'trig_status' : trig,                      # Trigger Flag (Bool Type)
      'trig_type' : trig_type,                   # Trigger Type (Character "G", "B", "U")

      }
    
    # Packet is transmitted 

    self.radio.send_data(**data_dict)


    
    
    
    


