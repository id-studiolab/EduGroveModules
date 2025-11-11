# Import necessary libraries
import time
import board
from adafruit_servokit import ServoKit
from adafruit_motorkit import MotorKit
from adafruit_pca9685 import PCA9685

# Initialize the I2C interface
i2c = board.I2C()  # Uses board's SCL and SDA pins

# Initialize the PCA9685 module for LED control
led = PCA9685(i2c, address=0x60)
led.frequency = 60  # Set the PWM frequency to 60Hz

# Initialize the ServoKit with 16 channels
servo = ServoKit(channels=16, i2c=i2c, address=0x60)

# Initialize the MotorKit
motor = MotorKit(i2c=i2c, address=0x60)

def fade_led_in(channel, steps=100, delay=0.0001):
    """
    Gradually increases the brightness of an LED on a specific channel.
    
    Args:
        channel (int): The channel number of the LED.
        steps (int): Number of steps to reach full brightness.
        delay (float): Delay between each step in seconds.
    """
    for i in range(steps):
        # Calculate the duty cycle value (0 to 0xFFFF)
        duty_cycle = int(0xFFFF * (i / steps))
        led.channels[channel].duty_cycle = duty_cycle
        time.sleep(delay)

def fade_led_out(channel, steps=100, delay=0.0001):
    """
    Gradually decreases the brightness of an LED on a specific channel.
    
    Args:
        channel (int): The channel number of the LED.
        steps (int): Number of steps to reach zero brightness.
        delay (float): Delay between each step in seconds.
    """
    for i in range(steps):
        # Calculate the duty cycle value (0 to 0xFFFF)
        duty_cycle = int(0xFFFF * ((steps - i) / steps))
        led.channels[channel].duty_cycle = duty_cycle
        time.sleep(delay)
    # Ensure the LED is fully off at the end
    led.channels[channel].duty_cycle = 0x0000

# Main loop
while True:
    # Fade the LED on channel 0 in and out
    fade_led_in(15)
    time.sleep(0.1) 
    fade_led_out(15)
    time.sleep(0.1)
    
    # Move the servo on channel 0 to 180 degrees
    servo.servo[14].angle = 180
    time.sleep(1)
    # Move the servo back to 0 degrees
    servo.servo[14].angle = 0
    time.sleep(1)

    # Set the motor1 throttle to full forward
    motor.motor1.throttle = 1.0
    time.sleep(1)
    # Stop the motor
    motor.motor1.throttle = 0
    time.sleep(1)
    # Set the motor1 throttle to full reverse
    motor.motor1.throttle = -1.0
    time.sleep(1)
    # Stop the motor
    motor.motor1.throttle = 0
    time.sleep(1)