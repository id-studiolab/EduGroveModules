"""
Example usage of the IMU_library for LSM6DS3.
This relatively simple version shows the basic use of the library.
"""

import time
import board
import sys
from IMU_library import IMU

# --- Determine I2C pins depending on the board. Important to allow for new and old boards! ---
print(sys.platform)
if sys.platform == "RP2350":  # Raspberry Pi Pico / Pico 2W
    import busio
    # Adjust these pins to your wiring
    i2c = busio.I2C(scl=board.GP5, sda=board.GP4)
else:
    # Default board.I2C() works for ItsyBitsy RP2040 and most Adafruit boards
    i2c = board.I2C()

# --- Initialize the filter using default I2C bus (board.I2C()) ---
imu = IMU(i2c=i2c)

# --- Set desired update rate for the IMU calculations (100Hz is a sensible update rate) ---
desired_update_hz = 100
update_interval = 1.0 / desired_update_hz
last_update_time = time.monotonic()

# --- Set desired rate for outputting relevant information to Serial (a fairly slow process that generally shouldn't be done at more than 5Hz) ---
desired_output_hz = 1
output_interval = 1.0/desired_output_hz
last_output_time = time.monotonic()

while True:
    # --- Check the current time for loop control ---
    current_time = time.monotonic()

    # --- Update the IMU values at the desired update rate (typically 100Hz) ---
    if current_time - last_update_time >= update_interval:
        last_update_time += update_interval
        imu.update()

    # --- Output data at the desired rate. Alternatively, this could be where you do additional processing ---
    if current_time - last_output_time >= output_interval:
        last_output_time += output_interval

        # --- Get latest IMU values. Other sensors could also be checked here ---
        # Angle estimates (roll = rotation around X, pitch = rotation around Y and yaw = rotation around Z)
        roll, pitch, yaw = imu.angle_estimates
        # Angular rates
        gx, gy, gz = imu.angular_rates

        # Print angle estimates
        print("Angle estimates (deg):")
        print("  Roll:", roll)
        print("  Pitch:", pitch)
        print("  Yaw:", yaw)

        # Print angular rates
        print("Angular rates (deg/s):")
        print("  gx:", gx)
        print("  gy:", gy)
        print("  gz:", gz)


