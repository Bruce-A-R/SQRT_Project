"""
trigering_algorithm.py

This script will run the triggering algorithm and be adopted to run in the
SQRT script

It is alone as a script for now for testing the actual function operations,
NO IMPORTS EXCEPT MATH :( if we even need that
"""

def parse_files_triggering(pressure_file, gps_file):
    """Function to parse saved text files of pressure and altitude into dict objects
        for use in the triggering algorithm.
        Inputs: names to files
        Outputs: dicts for timestamped pressure data and timestamped altitude data
    """
    pass

def check_pressure(pressure_value):
    """Function to check if a pressure value is above a set threshold
        Input: pressure value
        Output: True/False
    """

    if pressure_value <= 35:     # assuming pressure value in units of mbar
        return True
    else : return False

def check_altitude(altitude_value):
    """Function to check if an altitude value is above a set threshold
        Input: altitude value
        Output: True/False
    """

    if altitude_value >= 23:     # assuming altitude value in units of km
        return True
    else: return False

def check_falling(timestamped_altitudes_dict):
    """Function to check if the tuppersat is decending based on timestamps and corresponding altitudes
        This assumes that a dictionary of timestamps and altitudes exists to be inputted
        Inputs: dict of timestamps and altitude values
        Output: True/False
    """
    if timestamped_altitudes_dict["altitude"][-1] > 2000:     # assuming altitude in km, first check is we'rve above 2000km 
        
        decreases_list = []
        for i in range(len(timestamped_altitudes_dict["altitude"] - 1)):
            if timestamped_altitude_dict["altitude"][i+1] > timestamped_altitude_dict["altitude"][i]:
                decreases_list.append("d")
    
        if len(decreases_list) >= 10:    # arbitrary if 10 altitude readings of decreasing altitude, TBC
            return True
        else: return False

    else: return False

def check_pressure_sensor_failure(pressure_dict, altitude_dict):
    """Function to check if there is something wrong with the pressure sensor
        Inputs: dictionary of timestamped pressure sensor readings, dictionary of timestamped altitude readings
        Outputs: True/False

        types of pressure sensor isseues: 
        1. It is filled with Nones
        2. The pressure is consisently increasing with altitude
        3. pressure values look random
        4. pressure values are unchanging 
    """
    pass


# actual trigger check:

def trigger_check(pressure_file_name, gps_file_name): 
    """Function to run triggering check
        Priority: check pressure
        Secondary check: check altiude and if pressure sensor is bugging
        Ugly third check: check if tuppersat is descending

        Inputs: paths to text files for pressure sensor and gps sensor data
        
        Outputs: True/False, 
                type of trigger condition as string: "G", "B", or "U",
                for priority, secondary and tertiary checks

        run IF flag for already having triggered is False
    """

    pressure_dict, altitude_dict = parse_files_triggering(pressure_file_name, gps_file_name)      # parsing txt files

    # pressure check:
    if check_pressure(pressure_dict[-1]) == True:      # pressure trigger
        return True, "G"
    elif check_altitude(altitude_dict[-1]) == True and check_pressure_sensor_failure(pressure_dict, altitude_dict) == True :
        return True, "B"
    elif check_falling(altitude_dict) == True:
        return True, "U"
    else:
        return False

            
