class SQRT_trigger:
    """SQRT Triggering Algorithm class

    BR version as of 11/3

    Used to check for contitions to trigger our servo motor (to open the valve)
    How to use:
    1. Have a flag in the main tuppersat loop that triggering has or hasnt happened,
    and only run the check if it hasn't happened yet
    2. trigger_check will return both True/False trigger and the condition type of triggering
    
    """
    
    def __init__(self, pressure_file, gps_file, trigger_file):
        self.pressure_dict, self.gps_dict = self._parse_files_triggering(pressure_file, gps_file)

    def _parse_files_triggering(self, pressure_file, gps_file):
        """Function to parse saved text files of pressure and altitude into dict objects
            for use in the triggering algorithm.
            Inputs: names to files
            Outputs: dicts for timestamped pressure data and timestamped altitude data
        """
        # first parsing pressure file: the values go timestamp, pressure in cetnimbar, temperature in centiC
    
        pressure_dict = {
            'timestamp' : [],    # ms or mabe s actually?
            'pressure' : [],     # units of mbar
            'temperature' : [],     # C
        }
    
        with open(pressure_file, 'r') as file:
            lines = file.readlines()
            
            for i, line in enumerate(lines): 
                if i > 0:                      # to skip the first line that is saying collumn key
                    values = line.split(",")
                    
                    pressure_dict['timestamp'].append(int(values[0]))
                    pressure_dict['pressure'].append(float(values[1]) / 100)
                    pressure_dict['temperature'].append(float(values[2][:-2]) / 100)     # leave off the last 2 characters in the string cuz they are all "\n"
    
        #now gps file:
    
        gps_dict = {
            "timestamp" : [],    # ms
            "altitude": []       # m
        }
    
        with open(gps_file, 'r') as file:
            lines = file.readlines()
    
            for i, line in enumerate(lines):
                if i > 0:
                    values = line.split(",")
                    gps_dict["timestamp"].append(float(values[0]))
                    gps_dict["altitude"].append(float(values[3]))
    
                    
            #gps_dict["timestamp"].append(float(values[0]))
            #gps_dict["altitude"].append(float(values[3]))  # leave off the last 2 characters in the string cuz they are all "\n"
        
        return pressure_dict, gps_dict
    
    def _check_pressure(self, pressure_value):
        """Function to check if a pressure value is above a set threshold
            Input: pressure value
            Output: True/False
        """
        print(f"reading pressure: {pressure_value}")
        if pressure_value <= 35:     # assuming pressure value in units of mbar
            return True
        else : return False
    
    def _check_altitude(self, altitude_value):
        """Function to check if an altitude value is above a set threshold
            Input: altitude value
            Output: True/False
        """
    
        if altitude_value >= 22000:     # assuming altitude value in units of m, currenlty set to above 22 km but we could make it 23 km
            return True
        else: return False
    
    def _check_falling(self, altitudes_dict):
        """Function to check if the tuppersat is decending based on timestamps and corresponding altitudes
            This assumes that a dictionary of timestamps and altitudes exists to be inputted
            Inputs: dict of timestamps and altitude values
            Output: True/False
        """
        if altitudes_dict["altitude"][-1] > 2000:     # assuming altitude in km, first check is we'rve above 2000km 
            
            decreases_list = []
            
            try:
                for i in range(len(altitudes_dict["altitude"] - 1)):
                    #if altitude_dict["altitude"][i+1] > timestamped_altitude_dict["altitude"][i]: # wrong sequence I think its backwards
                    if altitudes_dict["altitude"][len(altitudes_dict["altitude"] - i)] << altitudes_dict["altitude"][len(altitudes_dict["altitude"] - i + 1)]: 
                        decreases_list.append("d")
            
                if len(decreases_list) >= 10:    # arbitrary if 10 altitude readings of decreasing altitude, TBC
                    return True
                else: return False
                    
            except:      # probably need to specify exceptions (ie: list to short, list doesn't exist)
                return False
    
        else: 
            return False
    
    def _check_pressure_sensor_failure(self, pressure_dict, altitude_dict):
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
        elif len(nones_list) >= len(pressure_dict["pressure"]) / 2:     # more than half the pressures are Nones
            return True
        elif pressure_dict["pressure"][0] == pressure_dict["pressure"][-1]:     # basic and not done check that the values r the same
            return True
        else: 
            return False
    
    
    # actual trigger check:
    
    def trigger_check(self.pressure_file, self.gps_dict, self.trigger_file): 
        """Function to run triggering check
            Priority: check pressure
            Secondary check: check altiude and if pressure sensor is bugging
            Ugly third check: check if tuppersat is descending
    
            should save a timestamped line of trigger check result and condition to
            the trigger log file
            
            should also return the check 
        """
    
        
        pressure_dict, gps_dict = parse_files_triggering(pressure_file, gps_file)


        #pressure_flag = check_pressure(self.pressure_dict['pressure'][-1])
        #print(pressure_flag)
        print(self.pressure_dict['pressure'][-1])
        print(self.gps_dict['altitude'][-1])
        try:
            if check_pressure(self.pressure_dict['pressure'][-1]) == True:      # pressure trigger
                check = True
                condition = "G"
            elif check_altitude(self.gps_dict['altitude'][-1]) == True and check_pressure_sensor_failure(pressure_dict, gps_dict) == True :
                check = True
                condition = "B"
            elif check_falling(self.gps_dict) == True:
                check = True
                condition = "U"
            else:
                check = False
                condition = "None"
        except:    
            print("exception in triggering check")
            check = False
            condition = "None"
            
        # now actually saving to a file:
        
        with open(self.trigger_file, "a") as file:
            file.write(f"{time.time()}, {check}, {condition}")
        
        #tests:
        print(check)
        print(condition)
        
        return check
