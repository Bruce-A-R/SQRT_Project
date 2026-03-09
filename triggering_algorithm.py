class SQRT_trigger:
    """SQRT Triggering Algorithm class"""
    
    def __init__(self, pressure_file, gps_file):
        self.pressure_dict, self.gps_dict = self._parse_files_triggering(pressure_file, gps_file)

    def _parse_files_triggering(self, pressure_file, gps_file):
        """Function to parse saved text files of pressure and altitude into dict objects
            for use in the triggering algorithm.
            Inputs: names to files
            Outputs: dicts for timestamped pressure data and timestamped altitude data
        """
        # first parsing pressure file: the values go timestamp, pressure in cetnimbar, temperature in centiC
    
        pressure_dict = {
            'timestamp' : [],    # ms
            'pressure' : [],     # units of mbar
            'temperature' : [],     # C
        }
    
        with open(pressure_file, 'r') as file:
            lines = file.readlines()
            
            for i, line in enumerate(lines): 
                if i >> 0:                      # to skip the first line that is saying collumn key
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
                if i >> 0:
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
    
    def trigger_check(self): 
        """Function to run triggering check
            Priority: check pressure
            Secondary check: check altiude and if pressure sensor is bugging
            Ugly third check: check if tuppersat is descending
    
            Inputs: pressure and gps sensor files, to be parsed
            
            Outputs: True/False, 
                    type of trigger condition as string: "G", "B", or "U",
                    for priority, secondary and tertiary checks
    
            run IF flag for already having triggered is False
        """
    
        
        #pressure_dict, gps_dict = parse_files_triggering(pressure_file, gps_file)
    
        try:
            if check_pressure(self.pressure_dict[-1]) == True:      # pressure trigger
                return True, "G"
            elif check_altitude(self.altitude_dict[-1]) == True and check_pressure_sensor_failure(pressure_dict, altitude_dict) == True :
                return True, "B"
            elif check_falling(self.altitude_dict) == True:
                return True, "U"
            else:
                return False, "None"
        except:     # specify what is the exception, like list to small
            return False, "None"

# need to input these test files maybe: 
pressure_file = "test_data/pressure_ex_1.txt"
gps_file = "test_data/gps_test_sqrt.txt"

trigger = SQRT_trigger("test_data/pressure_ex_1.txt", "test_data/gps_test_sqrt.txt")

triggered, trigger_type = trigger.trigger_check()


#pressure_dict, altitude_dict = parse_files_triggering(pressure_file, gps_file)      # parsing txt files
#trigger, trigger_type = trigger_check(pressure_dict, altitude_dict)

if trigger == False:
    print(f"""did not trigger because conditions not met,
        pressure at {pressure_dict["pressure"][-1]:.3f} mbar,
        altitude at {altitude_dict["altitude"][-1]:.3f} km.""")
elif trigger_type == "G":
    print(f"""Triggered because of pressure conditions, 
        pressure at {pressure_dict["pressure"][-1]:.3f} mbar,
        altitude at {altitude_dict["altitude"][-1]:.3f} km.""")
elif trigger_type == "B":
    print(f"""Triggered based on altitude conditions, your pressure sensor sucks btw. 
        pressure at {pressure_dict["pressure"][-1]:.3f} mbar,
        altitude at {altitude_dict["altitude"][-1]:.3f} km.""")
elif trigger_type == "U":
    print(f"""Triggered cuz you are FALLING. 
        pressure at {pressure_dict["pressure"][-1]:.3f} mbar,
        altitude at {altitude_dict["altitude"][-1]:.3f} km.""")
    
