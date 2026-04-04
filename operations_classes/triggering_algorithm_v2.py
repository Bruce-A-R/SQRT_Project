import time
from helper import Helper

helper = Helper()



class SQTtrigger:
    """SQRT Triggering Algorithm class

    current use (31/3):
    send lists and values to functions needed
    -BR
    
    Used to check for contitions to trigger our servo motor (to open the valve), and then do a longer run of thermal photos
    How to use:
    1. Have a flag in the main tuppersat loop that triggering has or hasnt happened,
    and only run the check if it hasn't happened yet
    2. trigger_check will return both True/False trigger and the condition type of triggering
    
    """

    def __init__(self):
        print("trigger algo ready")

    def _check_pressure(self, pressure_value):
        """Function to check if a pressure value is above a set threshold
            Input: pressure value
            Output: True/False
        """
        #print(f"reading pressure: {pressure_value}")
        
        if not pressure_value:
            return False
        elif float(pressure_value) <= 35: # changed from 35.0 for testing 35.0:     # assuming pressure value in units of mbar
            return True
        else : return False
    
    def _check_altitude(self, altitude_value):
        """Function to check if an altitude value is above a set threshold
            Input: altitude value
            Output: True/False
        """
        try:
            if float(altitude_value) >= 23000.0:     # assuming altitude value in units of m, currenlty set to above 23 km
                return True
            else: return False
        except Exception as e:
            #print(f"EXCEPTION IN READING ALTITUDE: {e}")
            return False
    
    def _check_falling(self, altitudes_list):
        """Function to check if the tuppersat is decending based on timestamps and corresponding altitudes
            This assumes that a dictionary of timestamps and altitudes exists to be inputted
            Inputs: dict of timestamps and altitude values
            Output: True/False
        """
        
        if altitudes_list[-1] > 2000:   # first check that sat is above 2km
            
            r_altitudes = altitudes_list[::-1]
            
            decreases_count = 0
            
            
            for i in range(len(r_altitudes)):              # done to get rid of "None"s that might be in the list
                if isinstance(r_altitudes[i], str):
                    r_altitudes.pop(i)
                elif r_altitudes[i] == None:
                    r_altitudes.pop(i)
            
            try:
                for i in range(len(r_altitudes) - 1):
                    if r_altitudes[i] < r_altitudes[i + 1] and r_altitudes[i] != 0:
                        decreases_count += 1

                if decreases_count >=3:
                    #print(f"True. {decreases_count}")
                    return True
                else:
                    #print(f"False. {decreases_count}")
                    return False
            
            except Exception as e:           #if list to short, just return false but also print error anyways just in case
                #print(f"Exception in falling trigger check: {e}")
                return False
    
        else:
            return False
    
    def _check_pressure_sensor_failure(self,pressure_list, altitude_list):
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
            
        for i in range(len(presure_list)):
            if presure_list[i] == None:
                nones_list.append(1)
    
        if len(pressure_list) == 0:     # never collected pressures
            return True
        #elif pressure_dict["pressure"][0] == pressure_dict["pressure"][-1]:     # basic and not done check that the values r the same
        #    return True
        elif nones_list == len(pressure_list):
            return True
        
        elif len(pressure_list) != len(altitude_list):       #if the pressures and altitudes somehow aren't the same length
            return True
        
        else: 
            return False
    
    
    # actual trigger check:
    
    def trigger_check(self, pressure, altitude, alt_list, pressure_list, file_list): 
        """Function to run triggering check
            Priority: check pressure
            Secondary check: check altiude and if pressure sensor is bugging
            Ugly third check: check if tuppersat is descending
    
            Inputs: pressure value, altitude value (both vurrent values in boolean form), list of boolean altitude values
            Outputs: check (boolean), condition (string), pressure value used (float), alt value used (float)
        """
        try:
            check = False
            condition = "None"

            if not pressure:
                pressure = "None"
                
            if not altitude:
                altitude = "None"
            
            try:
                if self._check_pressure(pressure) == True:      # pressure trigger
                    check = True
                    condition = "G"
                elif self._check_altitude(altitude) == True and self._check_pressure_sensor_failure(pressure_list, alt_list) == True :
                    check = True
                    condition = "B"
                elif self._check_falling(alt_list) == True:
                    check = True
                    condition = "U"
                else:
                    check = False
                    condition = "None"
            except Exception as e:    
                #print(f"exception in triggering check: {e}")
                check = False
                condition = "None"
                print(f"EXCPETION IN TRIGGERING WITH CHECKS SPECIFICALLY: {e}")
                helper.log_error(time.time(), e, "Trigger Checks", file_list[2])
                
            self.log_trigger(check, condition, pressure, altitude, file_list)

            return check, condition, pressure, altitude
        
        except Exception as e:
            check = False
            condition = None
            
            helper.log_error(time.time(), e, "Trigger Check", file_list[2])
            self.log_trigger(check, condition, pressure, altitude, file_list)
            
            print(f"EXCEPTION IN TRIGGERING CHECK: {e}")
            return check, condition, pressure, altitude
        
        
    def log_trigger(self, check, condition, pressure, altitude, file_list):
        """Function to log the trigger checks to the trigger check log"""
        try:
            with open(file_list[3], "a") as file:
                file.write(f"{check}, {condition}, {pressure}, {altitude} \n")
        except Exception as e:
            helper.log_error(time.time(), e, "Writing Trigger Check Log", file_list[2])
        
