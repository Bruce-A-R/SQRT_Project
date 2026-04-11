"""
servo_2.py

Author: Javi Ayuso
Version Date: 8/3/2026

Description: 

Contains servo script used to run the servo if trigger is True. 
The servo is made to move 90 degrees when activated

"""


import time
from machine import Pin, PWM

class Servo:
    """Class for activating the servo motor (part of valve system)"""

    def __init__(self):
        self.angle = 40   # set diff later?
        self.pin_number = 20     # could set it here but for now it is not, should be inputted when calling function
        self.frequency = 50

    def _set_angle(self, pwm, angle):
        """Funciton to set angle of servo arm using
        Inputs: pwm and angle
        Output: moves angle
        """
        # Convert angle to duty cycle (16-bit)
        min_duty = 1638   # ~1ms pulse  = 0°
        max_duty = 7864   # ~2ms pulse  = 180°
        duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
        pwm.duty_u16(duty)
        
    def run_servo(self):
        elnueve = PWM(Pin(self.pin_number))
        elnueve.freq(self.frequency)
        
        self._set_angle(elnueve, 30)
        time.sleep(1.0)
        
        elnueve.deinit()
        set_angle(elnueve, 90)  
        
        elnueve.deinit()
