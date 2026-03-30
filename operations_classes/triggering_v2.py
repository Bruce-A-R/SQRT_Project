class SQTtrigger:
    """SQRT Triggering Algorithm class

    current use (30/3):
    will parse out values from one housekeeping file that has data from both the gps and pressure sensor (as well as temp sensors),
    and only one loop timestamp
    -BR
    
    Used to check for contitions to trigger our servo motor (to open the valve), and then do a longer run of thermal photos
    How to use:
    1. Have a flag in the main tuppersat loop that triggering has or hasnt happened,
    and only run the check if it hasn't happened yet
    2. trigger_check will return both True/False trigger and the condition type of triggering
    
    """

    def __init__(self):
        print("trigger algo ready")

    def _parse_files_triggering(self,  housekeeping_file): #pressure_file, gps_file):
        """Function to parse saved text files of pressure and altitude into dict objects
            for use in the triggering algorithm.
            Inputs: name of housekeeping file
            Outputs: dicts for timestamped pressure data and timestamped altitude data
        """
        # the housekeeping data is now all in one file, but I'll still read into two seperate dictionaries just to save
        # the time of editing the code 
    
        pressure_dict = {
            'timestamp' : [],    # ms or mabe s actually?
            'pressure' : [],     # units of mbar
            'temperature' : [],     # C
        }
        
        gps_dict = {
            "timestamp" : [],    # ms
            "altitude": []       # m
        }
        
        with open(housekeeping_file, 'r') as file:
            lines = file.readlines()
        
        if len(lines) > 1:
            line = lines[-1]                    # getting last line of data that is not collumn key
            values = line.split(",")
            
            try:
                pressure_dict['timestamp'].append(float(values[0]))
                gps_dict['timestamp'].append(float(values[0]))
            except:
                pressure_dict['timestamp'].append(time.time())
                gps_dict['timestamp'].append(time.time())
            
            try:
                pressure_dict['temperature'].append(float(values[1]))
            except:
                pressure_dict['temperature'].append(999) # appending 999 for pressure and temperautre if nothing there
                
            try:
                pressure_dict['pressure'].append(float(values[2]))
            except:
                pressure_dict['pressure'].append(999)
                
            try:
                gps_dict["altitude"].append(float(values[7]))
            except:
                gps_dict["altitude"].append("NaN")
        
        return pressure_dict, gps_dict
    
    
    def _check_pressure(self, pressure_value):
        """Function to check if a pressure value is above a set threshold
            Input: pressure value
            Output: True/False
        """
        print(f"reading pressure: {pressure_value}")
        if float(pressure_value) <= 200.0: # changed from 35.0 for testing 35.0:     # assuming pressure value in units of mbar
            return True
        else : return False
    
    def _check_altitude(self,altitude_value):
        """Function to check if an altitude value is above a set threshold
            Input: altitude value
            Output: True/False
        """
    
        if float(altitude_value) >= 23000.0:     # assuming altitude value in units of m, currenlty set to above 23 km
            return True
        else: return False
    
    def _check_falling(self, altitudes_dict):
        """Function to check if the tuppersat is decending based on timestamps and corresponding altitudes
            This assumes that a dictionary of timestamps and altitudes exists to be inputted
            Inputs: dict of timestamps and altitude values
            Output: True/False
        """
        if float(altitudes_dict["altitude"][-1]) > 2000.0:     # assuming altitude in km, first check is we'rve above 2000km 
            
            decreases_list = []
            
            try:
                for i in range(len(altitudes_dict["altitude"] - 1)):
                    #if altitude_dict["altitude"][i+1] > timestamped_altitude_dict["altitude"][i]: # wrong sequence I think its backwards
                    if float(altitudes_dict["altitude"][len(altitudes_dict["altitude"] - i)]) < float(altitudes_dict["altitude"][len(altitudes_dict["altitude"] - i + 1)]): 
                        decreases_list.append("d")
            
                if len(decreases_list) >= 10:    # arbitrary if 10 altitude readings of decreasing altitude, TBC
                    return True
                else: return False
                    
            except:      # probably need to specify exceptions (ie: list to short, list doesn't exist)
                return False
    
        else: 
            return False
    
    def _check_pressure_sensor_failure(self,pressure_dict, altitude_dict):
        """Function to check if there is something wrong with the pressure sensor
            Inputs: dictionary of timestamped pressure sensor readings, dictionary of timestamped altitude readings
            Outputs: True/False
    
            types of pressure sensor isseues: 
            1. It is filled with Nones
            2. The pressure is consisently increasing with altitude
            3. pressure values look random
            4. pressure values are unchanging 
        """
    
        # setup tasks: 
        nones_list = []
            
        for i in range(len(presure_dict["pressure"])):
            if presure_dict["pressure"][i] == None:
                nones_list.append(1)
    
        if len(pressure_dict["pressure"]) == 0:     # never collected pressures
            return True
        elif pressure_dict["pressure"][0] == pressure_dict["pressure"][-1]:     # basic and not done check that the values r the same
            return True
        else: 
            return False
    
    
    # actual trigger check:
    
    def trigger_check(self, pressure_dict, gps_dict): 
        """Function to run triggering check
            Priority: check pressure
            Secondary check: check altiude and if pressure sensor is bugging
            Ugly third check: check if tuppersat is descending
    
            Inputs: parsed dict object from pressure file, parsed dict object from gps file
            Outputs: check (boolean), condition (string), pressure value used (float), alt value used (float)
        """
        
        check = False
        condition = "None"
        error = "None"

        if len(pressure_dict["pressure"]) == 0:
            presure = 'None'
            
            if len(gps_dict["altitude"])==0:
                altitude = "None"
            else: altitude = gps_dict['altitude'][-1]
            
            check = False
            condition = "None"
            print(f'trigger returns: {check},{condition}, {pressure}, {altitude}')
            return check, condition, pressure, altitude, error
            
            
            
        if len(gps_dict["altitude"])==0:
            altitude = "None"
            
            if len(pressure_dict["pressure"]) == 0:
                pressure = "None"
            else: pressure = pressure_dict['pressure'][-1]
            
            check = False
            condition = "None"
            print(f'trigger returns: {check}, {condition}, {pressure}, {altitude}')
            return check, condition, pressure, altitude, error
            
        #pressure_flag = check_pressure(self.pressure_dict['pressure'][-1])
        #print(pressure_flag)
        #print(pressure_dict['pressure'][-1])
        #print(gps_dict['altitude'][-1])
        
        pressure = pressure_dict['pressure'][-1]
        altitude = gps_dict['altitude'][-1]
        
        try:
            if self._check_pressure(pressure) == True:      # pressure trigger
                check = True
                condition = "G"
            elif self._check_altitude(altitude) == True and self._check_pressure_sensor_failure(pressure_dict, gps_dict) == True :
                check = True
                condition = "B"
            elif self._check_falling(gps_dict) == True:
                check = True
                condition = "U"
            else:
                check = False
                condition = "None"
        except Exception as e:    
            print(f"exception in triggering check: {e}")
            check = False
            error = f"exception in triggering check: {e}"
            condition = "None"
            
        # not saving directly to file anymore, instead returning check and condition type
        
       # with open(self.trigger_file, "a") as file:
        #    file.write(f"{time.time()}, {check}, {condition}")
        
        #tests:
        print(f'check: {check}')
        print(f'condition: {condition}')
        print(f'current pressure: {pressure}')
        print(f'current altitude: {altitude}')

    
        
        return check, condition, pressure, altitude, error
    
