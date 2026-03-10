class SQTGPS:
    """gps class SQTGPS, used to read out gps

    should read gps using set port and pins and then write reults to text file

    9/3/16 Bruce (this version likely wont work but we'll test it tomorrow)
    """


    def __init__(self, uart = 0, baudrate = 9600, tx_pin = 12, rx_pin = 13):
        """Funciton to initialze and connect to sensor"""
        self.gps = UART(uart, baudrate = baudrate, tx = Pin(tx_pin), rx = Pin(rx_pin))
        self.gps.init(baudrate, bits = 8, parity = None, stop = 1)                # taken from setup tasks 



    def _angle_reader(self, angle_string, hemisphere):
        """Takes an angle as a string in DDMM.MMMMM or 
        DDDMM.MMMMM format and return it as a float in decimal degrees
           
        Will also return angle as signed angle depending
        on the inputted hemishpere (N or S)
        """

        if len(angle_str) == 9:  #was 10:         # for DDMM.MMMMM format
            minutes = float(angle_str[2:10]) / 60
            degs = int(angle_str[0:2])
            
            ang = degs + minutes
            ang = sign_angle(ang, hemisphere)
            
            return ang
        
        elif len(angle_str) == 10:   #was 11:       # for DDDMM.MMMMM format
            minutes = float(angle_str[2:11]) / 60
            degs = int(angle_str[0:2])
            
            ang = degs + minutes
            ang = sign_angle(ang, hemisphere)
            
            return ang
        
        else:
            print("you messed up the string length")
            print(f"string length: {len(angle_str)}")
            
            return None


    def _sign_angle(self, angle, hemisphere):
        """Assigns a sign to the angle based on inputted hemisphere"""
        if hemisphere == 's' or hemisphere == 'W':
            angle = angle * -1

        return angle
    

    
    def _listen_for_sequence(self):              # not gonna pass a sequence cuz we're only looking for GGA
        """Function to listen for a inputted NMEA sequence (sequence_type) on a GPS serial port (port)
        Inputs: port and desired NMEA sequence. For this class the requested sequence will always be GGA
        Output: either None (if sentence is not of the requested type) or the sentence (if it 
        is of the requested type)
        """
        requested_sequence = None

        while port.any():
            data = port.readline()
            
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
        lat = angle_reader(split_sentence[2], split_sentence[3])
        lon = angle_reader(split_sentence[4], split_sentence[5])
        
        # assigning parts of the sequence to the dictiory keys
        if len(split_sentence[1]) != 0:
            mydict['timestamp'] = split_sentence[1]
        else:
            mydict['timestamp'] = None
    
        mydict['latitude'] = lat
        mydict['longitude'] = lon
        
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

    def gps_log(self, file_name):
        """Funciton to write the values we want from the read sequence to a text file. First it reads in data, 
        then it should save it all to a text file. It will loop reading from the GPS until it gets a GGA sequence
        Input: path to desired text file (should be on sd card) (string)
        Output: writes to that file
        """

        GGA = False
        gga_count = 0
        # reading and calibrating GPS data: 
        while GGA == False:
            
            time.sleep(1)
            sentence = listen_for_sequence(gps, 'GGA')
            
            if sentence is not None:
                # parsing sequence:
                dictionary = parse_sequence(sentence)
    
                # writing result string to the file
                with open(file_name, "a") as file:
                    file.write(f"{dictionary["timestamp"]},{dictionary["latitude"]},{dictionary["longitude"]},{dictionary["altitude"]}\n")
                
                gga_count += 1
            
            if gga_count == 10:
                GGA = True     # setting GGA flag so the listening loop can stop
