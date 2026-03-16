"""
gps.py

script with SQTGPS class in it that should initialize and read from gps

when called in the main loop, it should reutrn the values we want (lat, lon, altitude, timestamp, hdop) as a string
so we can write it to a file on the sd card

BR 15/3
"""

from machine import UART, Pin
import time

class SQTGPS:
    """gps class SQTGPS, used to read out gps

    reads and returns the values we want from a GGA sentence
    """


    def __init__(self, uart_bus, baudrate, tx_pin, rx_pin):
        """Funciton to initialze and connect to sensor"""
        print("Initialising")

            
        self.gps = UART(uart_bus, baudrate = baudrate, tx = tx_pin, rx = rx_pin)
            
        
        
        #try:
        #    self.devices = self.UART.scan()
        #    print(devices)
        #except Exception as e:
        #    print(f"exception to just fucking scanning for devices: {e}")
            
        #TAKING THIS PART OUT cuz it might be the part that is fucking everything up
        try:
            self.gps.init(baudrate, bits = 8, parity = None, stop = 1)                # taken from setup tasks 
        except Exception as e:
            print(f"init exception: {e}")
        

        gps_found = False
        try:
            for _ in range(10):
                if self.gps.any():
                    gps_found = True
                    print("found gps")
                    break
                else:
                    time.sleep(1)
                    
            print(f"gps found: {gps_found}")
# don't continue the loop if gps found
        except Exception as e:
            print(f" did not find GPS, and also: {e}")
            

        #while time.ticks_diff(time.ticks_ms(), start) < timeout:
        #    if self.gps.any():
        #        return
        #
        #raise RuntimeError("No GPS Found")

    def _angle_reader(self, angle_str, hemisphere):
        """Takes an angle as a string in DDMM.MMMMM or 
        DDDMM.MMMMM format and return it as a float in decimal degrees
           
        Will also return angle as signed angle depending
        on the inputted hemishpere (N or S)
        """

        if len(angle_str) == 9:  #was 10:         # for DDMM.MMMMM format
            minutes = float(angle_str[2:9]) / 60
            degs = int(angle_str[0:2])
            
            ang = degs + minutes
            ang = self.sign_angle(ang, hemisphere)
            
            return ang
        
        elif len(angle_str) == 10:   #was 11:       # for DDDMM.MMMMM format
            minutes = float(angle_str[3:10]) / 60
            degs = int(angle_str[0:3])
            
            ang = degs + minutes
            ang = sign_angle(ang, hemisphere)
            
            return ang
        
        else:
            print("you messed up the string length")
            print(f"string length: {len(angle_str)}")
            
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
            print(data)
            
            try:
                sentence = data.decode('ascii')
                print(sentence)
                sentenceid = sentence[3:6]
                if sentenceid == 'GGA':              # returns the sentece only if it is GGA
                    requested_sequence = sentence
            except UnicodeError:             # in case of error decoding
                print("unicode error, retrying")
            
        if requested_sequence:
            print(requested_sentence)
            return requested_sequence
        else:
            print("no sentence")
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
            'fields' : None
            }
        
        split_sentence = sequence.split(',')
        
        # converting lat and lon into degrees:
        lat = self.angle_reader(split_sentence[2], split_sentence[3])
        lon = self.angle_reader(split_sentence[4], split_sentence[5])
        
        # assigning parts of the sequence to the dictiory keys
        if len(split_sentence[1]) != 0:
            mydict['timestamp'] = split_sentence[1]
        else:
            mydict['timestamp'] = None
    
        mydict['latitude'] = lat
        mydict['longitude'] = lon
        mydict['hdop'] = split_sentence[8]
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
        
        return mydict

    def gps_log(self):
        """Funciton to write the values we want from the read sequence to a text file. First it reads in data, 
        then it should return the wanted values as a string to be saved to the sd card
        which will happen in the main function"""

        GGA = False
        gga_count = 0
        
        # reading and calibrating GPS data: 
        while GGA_count_done == False:
            
            time.sleep(1)
            sentence = self._listen_for_sequence()
            
            if sentence is not None:
                # parsing sequence:
                dictionary = self.parse_sequence(sentence)
    
                # making and returning result string
                
                print(f"{dictionary["timestamp"]},{dictionary["latitude"]},{dictionary["longitude"]},{dictionary["altitude"]}, {dictionary["hdop"]}\n")
                return f"{dictionary["timestamp"]},{dictionary["latitude"]},{dictionary["longitude"]},{dictionary["altitude"]}, {dictionary["hdop"]}\n"
                    
                
                
                
                gga_count += 1
     
            if gga_count_done == 10:
                GGA = True     # setting GGA flag so the listening loop can stop
                return f"{time.time()}, None, None, None, None, None \n"
                
