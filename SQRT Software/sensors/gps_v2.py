"""
gps_v2.py

Authors: Bruce Ritter, Caimin Keavney 
Version Date: 14/4/2026

Description:

This script contains SQTGPS class, which contains functions to initialize the gps, 
and to collect and calibrate gps data. 

"""

from machine import UART, Pin
import time
from gps_airborne import set_airborne_mode

class SQTGPS:
    """gps class SQTGPS, used to read out gps

    reads and returns the values we want from a GGA sentence
    """


    def __init__(self, uart_bus, baudrate, tx_pin, rx_pin):
        """Funciton to initialze and connect to sensor"""
        

        
        self.gps = UART(uart_bus, baudrate = baudrate, tx = tx_pin, rx = rx_pin)
        
        
        time.sleep(1)
        set_airborne_mode(self.gps)
            

    
    def _angle_reader(self, angle_str, hemisphere):
        """Takes an angle as a string in DDMM.MMMMM or 
        DDDMM.MMMMM format and return it as a float in decimal degrees
           
        Will also return angle as signed angle depending
        on the inputted hemishpere (N or S)
        """

        if len(angle_str) == 10:  #was 10:         # for DDMM.MMMMM format
            minutes = float(angle_str[2:9]) / 60
            degs = int(angle_str[0:2])
            
            ang = degs + minutes
            ang = self._sign_angle(ang, hemisphere)
            
            return ang
        
        elif len(angle_str) == 11:   #was 11:       # for DDDMM.MMMMM format
            minutes = float(angle_str[3:10]) / 60
            degs = int(angle_str[0:3])
            
            ang = degs + minutes
            ang = self._sign_angle(ang, hemisphere)
            
            return ang
        
        else:
            print("no angle")
            return None


    def _sign_angle(self, angle, hemisphere):
        """Assigns a sign to the angle based on inputted hemisphere"""
        if hemisphere == 'S' or hemisphere == 'W':
            angle = angle * -1

        return angle
    

    
    def _listen_for_sequence(self):              # not gonna pass a sequence cuz we're only looking for GGA
        """Function to listen for a inputted NMEA sequence (sequence_type) on a GPS serial port (port)
        Inputs: port and desired NMEA sequence. For this class the requested sequence will always be GGA
        Output: either None (if sentence is not of the requested type) or the sentence (if it 
        is of the requested type)
        """
        requested_sequence = None
        
        

        
        while self.gps.any():

            data = self.gps.readline()

            
            try:
                sentence = data.decode('ascii')
                sentenceid = sentence[3:6]
                if sentenceid == 'GGA':              # returns the sentece only if it is GGA
                    requested_sequence = sentence
            except UnicodeError:             # in case of error decoding
                print("unicode error, retrying")
                
            if requested_sequence:
                return requested_sequence
        
        else:
            print("no sentence,  still listening")
            return None

    def _parse_sequence(self, sequence):
        """Function to parse sequnce and return values that we want to save to a text file
        For now this makes a dictionary off all the GGA fields but we really only care about
        Lon, Lat, Alt, and timestamps for measurements. 
        Inputs: sequence (string)
        Output: dictionary of fields in the sequence
        """
        
        # creating dictionary to fill with values
        mydict = {             
            'longitude' : None,
            'latitude' : None,
            'altitude' : None,
            'timestamp' : None,
            'sentence' : None,
            'checksum' : None,
            'fields' : None,
            'hdop' : None
            }
        
        split_sentence = sequence.split(',')
        
        if len(split_sentence) == 15:
                
            # converting lat and lon into degrees:
            lat = self._angle_reader(split_sentence[2], split_sentence[3])
            lon = self._angle_reader(split_sentence[4], split_sentence[5])
            
            # assigning parts of the sequence to the dictiory keys
            if len(split_sentence[1]) != 0:
                mydict['timestamp'] = split_sentence[1]
            else:
                mydict['timestamp'] = None
        
            mydict['latitude'] = lat
            mydict['longitude'] = lon
            
            if len(split_sentence[8]) != 0:
                mydict["hdop"] = split_sentence[8]
            else:
                
                mydict["hdop"] = None
                
            if len(split_sentence[9]) != 0:
                mydict['altitude'] = split_sentence[9]
            else: 
                mydict['altitude'] = None
            
            mydict['sentence'] = sequence
            
            if len(split_sentence[14]) != 0:
                mydict['checksum'] = split_sentence[14]
            else: 
                mydict['checksum'] = None
            
            mydict['fields'] = split_sentence
        else:
            mydict = None
        return mydict

    def gps_log(self):
        """Funciton to write the values we want from the read sequence to a text file. First it reads in data, 
        then it should return the wanted values as a string to be saved to the sd card or appended to a list in main
        Inputs: None
        Outputs: GPS time, lat, lon, alt, hdop (all values from read NMEA string)
        """

        GGA = False
        gga_count = 0
        
        # reading and calibrating GPS data: 
        while GGA == False:
            
            time.sleep(1)
            sentence = self._listen_for_sequence()
            
            
            if sentence is not None:
                # parsing sequence:
                print(sentence)
                dictionary = self._parse_sequence(sentence)
    
                # making and returning result string
                
                timestamp, lat, lon, alt, hdop = dictionary["timestamp"],dictionary["latitude"],dictionary["longitude"],dictionary["altitude"],dictionary["hdop"]
                
        
                return timestamp, lat, lon, alt, hdop
                    
            else:
                return None, None, None, None, 99.99
                
                
                gga_count += 1
     
            if gga_count == 5:
                GGA = True     # setting GGA flag so the listening loop can stop
                return None
                
