"""
gps_GGA_looped.py

This scripts will constantly listen for GGA sentences. It will parse GGA sentences and return
formatted results for timestamped latitude, longitude, and altitude. 

"""

# inputs:
from machine import UART, Pin
import time

def listen_for_sequence(port, sequence_type):
    """Function to listen for a inputted NMEA sequence (sequence_type) on a GPS serial port (port)
    Inputs: port and desired NMEA sequence
    Output: either None (if sentence is not of the requested type) or the sentence (if it 
    is of the requested type)
    """
    requested_sequence = None
    while port.any():
        data = port.readline()
        
        try:
            sentence = data.decode('ascii')
            sentenceid = sentence[3:6]
            if sentenceid == sequence_type:
                #returns the sentece only if it is GLL
                requested_sequence = sentence
        except UnicodeError: #in case of error decoding
            print("unicode error, retrying")
            pass
        
    if requested_sequence:
        return requested_sequence
    else:
        return None
        
def parse_sequence(sequence):
    """Function to parse sequnce and put values into a dictionary"""
    
    # creating dictionary to fill with values
    mydict = {             
        'longitude' : None,
        'latitude' : None,
        'altitude' : None,
        'timestamp' : None,
        'sentence' : None,
        'checksum' : None,
        'fields' : None
        }
    
    split_sentence = sequence.split(',')
    
    # converting lat and lon into degrees:
    lat = angle_reader(split_sentence[2], split_sentence[3])
    lon = angle_reader(split_sentence[4], split_sentence[5])
    
    # assigning parts of the sequence to the dictiory keys
    if len(split_sentence[1]) is not 0:
        mydict['timestamp'] = split_sentence[1]

    mydict['latitude'] = lat
    mydict['longitude'] = lon
    
    if len(split_sentence[9]) is not 0:
        mydict['altitude'] = split_sentence[9]
    
    mydict['sentence'] = sequence
    
    if len(split_sentence[14]) is not 0:
        mydict['checksum'] = split_sentence[14]
    mydict['fields'] = split_sentence
    
    return mydict

def angle_reader(angle_str, hemisphere):
    """Takes an angle as a string in DDMM.MMMMM or 
    DDDMM.MMMMM format and return it as a float in decimal degrees
   
    Will also return angle as signed angle depending
    on the inputted hemishpere (N or S)
    """
    
    if len(angle_str) == 10:         # for DDMM.MMMMM format
        minutes = float(angle_str[2:10]) / 60
        degs = int(angle_str[0:2])
        
        ang = degs + minutes
        ang = sign_angle(ang, hemisphere)
        
        return ang
    
    elif len(angle_str) == 11:       # for DDDMM.MMMMM format
        minutes = float(angle_str[2:11]) / 60
        degs = int(angle_str[0:2])
        
        ang = degs + minutes
        ang = sign_angle(ang, hemisphere)
        
        return ang
    
    else:
        print("you messed up the string length")
        print(f"string length: {len(angle_str)}")
        return None
     

def sign_angle(angle, hemisphere):
    """Assigns a sign to the angle based on inputted hemisphere"""
    if hemisphere == 'N':
        angle = angle
    elif hemisphere == 'S':
        angle = angle * -1
    elif hemisphere == 'E':
        angle = angle
    elif hemisphere == 'W':
        angle = angle * -1   
    
    return angle
    
def main():
    """Main function"""

    # setup:
    gps = UART(0, baudrate =9600 , tx=Pin(12), rx=Pin(13))
    gps.init(9600, bits =8 , parity=None , stop=1)
    list_of_dictionaries = []

    # seting up file to write to

   # creating txt file for sensor data: THIS ACTUALLY SHOULD HAPPEN OUTSIDE OF DATA COLLECTION LOOP THO
    with open("gps_log.txt", "a") as file:
        file.write("Timestamp, Lat, Lon, Alt \n")      # writting names for the values to be added

    # reading and calibrating GPS data: 

    time.sleep(1)
    sentence = listen_for_sequence(gps, 'GGA')
    
    if sentence is not None:
          # parsing sequence:
          dictionary = parse_sequence(sentence)

    # writing result string to the file
    with open("sensor_log.txt", "a") as file:
            file.write(f"{dictionary["timestamp"]},{dictionary["latitude"]},{dictionary["longitude"]},{dictionary["altitude"]}\n")
    #while True:
    #    time.sleep(1)
        
     #   sentence = listen_for_sequence(gps, 'GGA')       # GGA is the correct sentence to listen for
    
    #    if sentence is not None:
    
            # parsing sequence:
      #      dictionary = parse_sequence(sentence)
       #     list_of_dictionaries.append(dictionary)

            # printing results:
       #     print("Formatted results: ")
       #     print(f'Timestamp: {dictionary["timestamp"]}, Lat: {dictionary["latitude"]}, Lon: {dictionary["longitude"]}, Alt: {dictionary["altitude"]}')
       # 
      
if __name__ == '__main__': 
    main()
