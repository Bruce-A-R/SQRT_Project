import time
from machine import Pin, PWM

def set_angle(pwm, angle):
    # Convert angle to duty cycle (16-bit)
    min_duty = 1638   # ~1ms pulse  = 0°
    max_duty = 7864   # ~2ms pulse  = 180°
    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    pwm.duty_u16(duty)


elnueve = PWM(Pin(0))
elnueve.freq(50)

set_angle(elnueve, 40)
time.sleep(5.0)
set_angle(elnueve, 90)
time.sleep(5.0)
set_angle(elnueve, 30)
time.sleep(1.0)

elnueve.deinit()