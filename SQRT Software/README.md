## SQRT CODE

This file contains all the SQRT mission software. 
Code is updated as of 11/4/2026. 

## Directory

1. **main.py**: the main function that runs automatically when the onboard computer (Raspberry Pi Pico 2) is connected to power
2. **sensor classes/ :** this folder contains scripts with classes used to interface with the sensors onboard (GPS, ms5611 pressure sensor,
     ds18b20 temp sensors, MLX90640 thermal sensor)
3. **operations classes/ :** this folder contains scripts with both classes used to interface with non-sensor components (TTT comms module classes, servo motor class)
     and classes used for software operations (triggering algorithm, helper class).
