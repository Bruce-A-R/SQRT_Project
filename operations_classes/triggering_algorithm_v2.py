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

    def _check_pressure(self, pressure_value, file_list):
        """Function to check if a pressure value is above a set threshold
            Input: pressure value
            Output: True/False
        """
        #print(f"reading pressure: {pressure_value}")
        try:
            if not pressure_value:
                print('no pressure value')
                return False
            elif float(pressure_value) <= 35: # changed from 35.0 for testing 35.0:     # assuming pressure value in units of mbar
                return True
            else : return False
        except Exception as e:
            print(f'pressure check error: {e}')
            helper.log_error(time.time(), e, "Trigger Check: pressure under threshold check", file_list[2])
            return False
    
    def _check_altitude(self, altitude_value, file_list):
        """Function to check if an altitude value is above a set threshold
            Input: altitude value
            Output: True/False
        """
        try:
            if float(altitude_value) >= 23000.0:     # assuming altitude value in units of m, currenlty set to above 23 km
                print("ALT CHECK TRUE")
                return True
            else: return False
        except Exception as e:
            helper.log_error(time.time(), e, "Trigger Check: alt over threshold", file_list[2])
            return False
    
    def _check_falling(self, altitudes_list, file_list):
        """Function to check if the tuppersat is decending based on list of altitudes over time
            Inputs: list of altitudes (in order of time taken)
            Output: True/False (True if altitude has decreased for half of listed numbers)

            Function:
            - if half of altitudes list is more than 4, true if alt has decreased more than half of list length. 
            - if half of altitudes list is 4 or less (meaning 4+ values in the origional list were Nones), then see if alt has decreased >=4 times
            
            This is done becase there's a chance the sat is falling but GPS with its tolerance reads the same altitude value twice in a row,
            so we cant just do it if there are four+ (or half list length +) decreases in a row.
            
        """
        try:
            if altitudes_list[-1] > 2000:   # first check that sat is above 2km
                
                r_altitudes = altitudes_list[::-1]
                
                decreases_count = 0

                print(r_altitudes)

                #removing Nones and "None"s from the list if they are there:
                remove_list = ["None", None]
                new_r_altitudes = []

                for val in r_altitudes:
                    if val not in remove_list:
                        new_r_altitudes.append(val)

                r_altitudes = new_r_altitudes   #now should just be values with Nones and "None"s taken out

                print(r_altitudes)
                
                try:
                    for i in range(len(r_altitudes) -1):
                        if (r_altitudes[i] < r_altitudes[i + 1]) and r_altitudes[i] != 0:
                            decreases_count +=1                   

                    if len(r_altitudes) / 2 >= 4:
                        if decreases_count >= len(r_altitudes) / 2:
                            print(f"True. {decreases_count}")
                            return True
                        else:
                            print(f"False. {decreases_count}")
                            return False
                    else:
                        if decreases_count >= 4:
                            print(f"True. {decreases_count}")
                            return True
                        else:
                            print(f"False. {decreases_count}")
                            return False
                
                except Exception as e:           #if list to short, just return false but also print error anyways just in case
                    helper.log_error(time.time(), e, "Trigger Check: Falling Check. Not bad unless loop count > 12", file_list[2])
                    return False
        
            else:
                return False
        except Exception as e:
            helper.log_error(time.time(), e, "Trigger Check: Falling check", file_list[2])
            return False
    
    def _check_pressure_sensor_failure(self,pressure_list, file_list):
        """Function to check if there is something wrong with the pressure sensor
            Inputs: list of pressure sensor readings
            Outputs: True/False
    
            types of pressure sensor isseues: 
            1. It is filled with Nones
            2. pressure list is not there, or mostly empty
            3. pressure values are unchanging 
        """
        nones_list = []
        sames_list = []
        try:
            for i in range(len(pressure_list) - 1):
                if pressure_list[i] == pressure_list[i+1]:
                    sames_list.append(1)

            for i in range(len(pressure_list)):
                if pressure_list[i] == None:
                    nones_list.append(1)
            print(sames_list)
            if not pressure_list:    #never collected pressures or list is not in there correctly 
                return True
            elif len(pressure_list) == 0:     # never collected pressures
                return True
            elif nones_list == len(pressure_list):   #if list all Nones (never colelcted pressures
                return True
            elif len(sames_list) == len(pressure_list) -1:  #if all the pressure values are the same thing
                return True
                
            else: 
                return False
        except Exception as e:
            print(f"pressure issue check exception :{e}.")
            helper.log_error(time.time(), e, "Trigger Check: Falling Check", file_list[2])
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
                if self._check_pressure(pressure, file_list) == True:      # pressure trigger
                    check = True
                    condition = "G"
                elif self._check_altitude(altitude, file_list) == True and self._check_pressure_sensor_failure(pressure_list, file_list) == True :
                    check = True
                    condition = "B"
                elif self._check_falling(alt_list, file_list) == True:
                    check = True
                    condition = "U"
                else:
                    check = False
                    condition = "None"
            except Exception as e:    
                print(f"exception in triggering check: {e}")
                check = False
                condition = "None"
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
