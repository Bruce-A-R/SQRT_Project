"""
The code below will be used to collect relevant data, format telemetry/science data packets, and
interface with communications architecture.
"""
 
from datetime import datetime as dt
import os
import machine 
from tuppersat.radio import SatRadio

# Create UART object
uart = machine.UART(1, baudrate = 38400, tx = machine.Pin(16), rx = machine.Pin(17))

radio_settings = {
  'address' : 0x53,
  'callsign' : "SQT"
}

class Comms:
  def __init__(self):
      self.radio = SatRadio(uart, **radio_settings)

      # Counts initialised for determining packet numbers.
      self.t_packet_count = 0
      self.d_packet_count = 0

      # SD card file paths defined for data gathering.
      self.sd_files = {
        "External_TP": "/mnt/sdcard/external_readings.txt",
        "Internal_T": "/mnt/sdcard/thermo_readings.txt",
        "GPS": "/mnt/sdcard/gps_log.txt",
        "MLX": "/mnt/sdcard/mlx_readings.txt",
        "Servo": "/mnt/sdcard/servo_status.txt",
        "Trigger": "/mnt/sdcard/trig_status.txt",
        "Trigger_Type": "/mnt/sdcard/trig_type.txt"
        }



  def get_last_entry(self, filepath):
    """
    Reads the last line from a text file on the SD card.

    Inputs:
    filepath (str) - Filepath containing the relevant data.

    Returns:
    last_line (str) - The most recently appended line to the textfile.
    """
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
  
  def telem_packet(self):
    """
    Telemetry packet is formatted and sent.
    """
    # Packet Type is specified
    packet_type = 'T'

    # The telemetry data is collected from the corresponding files on the SD card.
    lat,lon,alt = self.get_last_entry(self.sd_files["GPS"]).split(',')[1:] 
    TE, P = self.get_last_entry(self.sd_files["External_TP"]).split(',')
    TI = self.get_last_entry(self.sd_files["Internal_T"])

    # Telemetry packet count is incremented.
    self.t_packet_count += 1
    
    telem_dict = {
      'hhmmss' : dt.now().strftime("%H%M%S"),
      'alt': alt,           # Altitude in metres
      'lat_deg' : lat,      # Latitude in degrees
      'lon_deg' : lon,      # Longitude in degrees
      'press' : P,          # External pressure in millibars
      'temp_E': TE,         # External temperature in Celsius
      'temp_I': TI,         # Internal temperature in Celsius
      
    }

    # The formatted data packet is transmitted 
    self.radio.start()
    self.radio.send_telemetry(packet_type, self.t_packet_count, **telem_dict)
    self.radio.stop()


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
    # Packet type is specified.
    packet_type = 'D'

    # Most recent thermal array is loaded in from the SD card and cropped for ease of transmission
    frame = [float(x) for x in self.get_last_entry(self.sd_files["MLX"]).split(',')]
    crop_frame = self.cropping(frame)

    # The current flag statuses are read in.
    servo_motor = self.get_last_entry(self.sd_files["Servo"])
    trig = self.get_last_entry(self.sd_files["Trigger"])
    trig_type = self.get_last_entry(self.sd_files["Trigger_Type"])

    # Data packet count is incremented
    self.d_packet_count += 1

    # Data dictionary is formatted.
    data_dict = {
      'hhmmss' : dt.now().strftime('%H%M%S'),    # Time in UTC
      'therm_array' : crop_frame,                # 48 temperature values (Celsius)
      'servo_flag' : servo_motor,                # Servo Motor flag (Bool Type)
      'trig_status' : trig,                      # Trigger Flag (Bool Type)
      'trig_type' : trig_type,                   # Trigger Type (Character "G", "B", "U")

      }
    # Packet is transmitted 
    self.radio.start()
    self.radio.send_telemetry(packet_type, self.d_packet_count, **data_dict)
    self.radio.stop()

    
    
    
    

