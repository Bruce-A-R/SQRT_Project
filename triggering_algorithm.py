"""
trigering_algorithm.py

This script will run the triggering algorithm and be adopted to run in the
SQRT script

It is alone as a script for now for testing the actual function operations
"""

def parse_files(pressure_file, altitude_file):
  """Function to parse saved text files of pressure and altitude into dict objects
    for use in the triggering algorithm.
    Inputs: names to files
  Outputs: dicts for timestamped pressure data and timestamped altitude data
  """

def check_pressure(pressure_value):
  """Function to check if a pressure value is above a set threshold
    Input: pressure value
    Output: True/False
    """

  if pressure_value <= 35 # assuming pressure value in units of mbar
    return True
  else : return False

def check_altitude(altitude_value):
  """Function to check if an altitude value is above a set threshold
    Input: altitude value
    Output: True/False
    """

  if altitude_value >= 23 # assuming altitude value in units of km
    return True
  else: return False

def check_falling(timestamped_altitudes_dict):
  """Function to check if the tuppersat is decending based on timestamps and corresponding altitudes
    This assumes that a dictionary of timestamps and altitudes exists to be inputted
    Inputs: dict of timestamps and altitude values
    Output: True/False
  """

  for i in range(len(timestamped_altitudes_dict)):
    if 
  
  
    
