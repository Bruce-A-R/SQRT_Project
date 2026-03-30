"""
servo_class.py

Editied servo script to make it a class usable in the main function
it should just move the servo 90 degrees when activated (I think)

"""


import time
from machine import Pin, PWM

class Servo:
    """Class for activating the servo motor (part of valve system)"""

    def __init__(self):
        self.angle = 40   # set diff later?
        #self.pin_number = 22     # could set it here but for now it is not, should be inputted when calling function
        self.frequency = 50

    def _set_angle(pwm, angle):
        """Funciton to set angle of servo arm using
        Inputs: pwm and angle
        Output: moves angle
        """
        # Convert angle to duty cycle (16-bit)
        min_duty = 1638   # ~1ms pulse  = 0°
        max_duty = 7864   # ~2ms pulse  = 180°
        duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
        pwm.duty_u16(duty)

    def activate_servo(pin):
        """function to run the servo
        Inputs: pin for OneWire pin connection
        Output: will change angle of servo, in this case just by 90 degrees and just once
        """
        elnueve = PWM(Pin(self.pin_number))
        elnueve.freq(self.frequency)

        set_angle(elnueve, 90)  
        
        elnueve.deinit()
