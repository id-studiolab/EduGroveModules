"""
Optimized IMU library for use with the LSM6DS3
- Faster update rate on CircuitPython
- Quaternion-based complementary filter
- Euler angles and angular rates accessible on demand
"""

import time
import math
import board
import adafruit_lsm6ds.lsm6ds3 as LSM6DS3
from adafruit_lsm6ds import Rate

class IMU:
    def __init__(self, i2c=None,
                 accel_rate=Rate.RATE_104_HZ,
                 gyro_rate=Rate.RATE_104_HZ,
                 alpha=0.98,
                 norm_every=5,
                 accel_corr_every=2):

        if i2c is None:
            i2c = board.I2C()
        self.sensor = LSM6DS3.LSM6DS3(i2c)

        self._accel_rate = accel_rate
        self._gyro_rate = gyro_rate
        self._alpha = alpha

        self.sensor.accelerometer_data_rate = accel_rate
        self.sensor.gyro_data_rate = gyro_rate

        # Quaternion state
        self.q = [1.0, 0.0, 0.0, 0.0]

        # Calibration offsets
        self.gyro_offset = (0.0, 0.0, 0.0)
        self.accel_offset = (0.0, 0.0, 0.0)

        # Timing
        self._last_time = time.monotonic()
        self._warn_interval = 1.0
        self._last_warn_time = 0.0
        self._dt_history = []

        # Optimization parameters
        self._update_count = 0
        self._norm_every = norm_every
        self._accel_corr_every = accel_corr_every

        # Cached Euler angles to avoid recomputation every loop
        self._roll = 0.0
        self._pitch = 0.0
        self._yaw = 0.0

    # ---------------- Calibration ----------------
    def calibrate(self, duration=2.0):
        print("Calibration started: keep the sensor still and flat...")
        start = time.monotonic()
        gx_vals, gy_vals, gz_vals = [], [], []
        ax_vals, ay_vals, az_vals = [], [], []

        while time.monotonic() - start < duration:
            ax, ay, az = self.sensor.acceleration
            gx, gy, gz = self.sensor.gyro
            ax_vals.append(ax); ay_vals.append(ay); az_vals.append(az)
            gx_vals.append(gx); gy_vals.append(gy); gz_vals.append(gz)
            time.sleep(0.01)

        self.accel_offset = (
            sum(ax_vals)/len(ax_vals),
            sum(ay_vals)/len(ay_vals),
            sum(az_vals)/len(az_vals) - 9.81
        )
        self.gyro_offset = (
            sum(gx_vals)/len(gx_vals),
            sum(gy_vals)/len(gy_vals),
            sum(gz_vals)/len(gz_vals)
        )
        print("Calibration complete.")
        print("Gyro offsets (rad/s):", self.gyro_offset)
        print("Accel offsets (m/s^2):", self.accel_offset)
        self._last_time = time.monotonic()

    def set_offsets(self, gyro_offset, accel_offset):
        self.gyro_offset = gyro_offset
        self.accel_offset = accel_offset

    # ---------------- Update ----------------
    def update(self):
        now = time.monotonic()
        dt = now - self._last_time
        self._last_time = now

        # --- Monitor update rate ---
        self._dt_history.append(dt)
        if len(self._dt_history) > 100:
            self._dt_history.pop(0)

        if len(self._dt_history) >= 10:
            avg_dt = sum(self._dt_history)/len(self._dt_history)
            if avg_dt > 0.0125:
                if now - self._last_warn_time > self._warn_interval:
                    print(f"Warning: update() running too slowly (~{1/avg_dt:.1f} Hz)")
                    self._last_warn_time = now

        # --- Read sensors & apply offsets ---
        ax, ay, az = self.sensor.acceleration
        gx, gy, gz = self.sensor.gyro
        ax -= self.accel_offset[0]; ay -= self.accel_offset[1]; az -= self.accel_offset[2]
        gx -= self.gyro_offset[0]; gy -= self.gyro_offset[1]; gz -= self.gyro_offset[2]

        # --- Quaternion integration ---
        q0, q1, q2, q3 = self.q
        q_dot = (
            0.5 * (-q1*gx - q2*gy - q3*gz),
            0.5 * ( q0*gx + q2*gz - q3*gy),
            0.5 * ( q0*gy - q1*gz + q3*gx),
            0.5 * ( q0*gz + q1*gy - q2*gx)
        )
        self.q[0] += q_dot[0]*dt
        self.q[1] += q_dot[1]*dt
        self.q[2] += q_dot[2]*dt
        self.q[3] += q_dot[3]*dt

        # --- Normalize quaternion every N updates ---
        self._update_count += 1
        if self._update_count % self._norm_every == 0:
            self.q = self._normalize_quat(self.q)

        # --- Accelerometer correction every N updates ---
        if self._update_count % self._accel_corr_every == 0:
            norm = math.sqrt(ax*ax + ay*ay + az*az)
            if norm > 0:
                ax /= norm; ay /= norm; az /= norm
                accel_roll = math.atan2(ay, az)
                accel_pitch = math.atan2(-ax, math.sqrt(ay*ay + az*az))
                roll, pitch, yaw = self._quat_to_euler(self.q)
                roll = self._alpha*roll + (1 - self._alpha)*accel_roll
                pitch = self._alpha*pitch + (1 - self._alpha)*accel_pitch

                cy = math.cos(yaw*0.5); sy = math.sin(yaw*0.5)
                cp = math.cos(pitch*0.5); sp = math.sin(pitch*0.5)
                cr = math.cos(roll*0.5); sr = math.sin(roll*0.5)

                self.q = [
                    cr*cp*cy + sr*sp*sy,
                    sr*cp*cy - cr*sp*sy,
                    cr*sp*cy + sr*cp*sy,
                    cr*cp*sy - sr*sp*cy
                ]

        # --- Euler angles are computed only when accessed ---
        # No unnecessary trigonometry here

    # ---------------- Accessors ----------------
    @property
    def angle_estimates(self):
        """Return roll, pitch, yaw in degrees."""
        roll, pitch, yaw = self._quat_to_euler(self.q)
        return math.degrees(roll), math.degrees(pitch), math.degrees(yaw)

    @property
    def angular_rates(self):
        gx, gy, gz = self.sensor.gyro
        gx -= self.gyro_offset[0]; gy -= self.gyro_offset[1]; gz -= self.gyro_offset[2]
        return math.degrees(gx), math.degrees(gy), math.degrees(gz)

    @property
    def update_rate_hz(self):
        if not self._dt_history: return 0.0
        avg_dt = sum(self._dt_history)/len(self._dt_history)
        return 1/avg_dt

    # ---------------- Quaternion helpers ----------------
    @staticmethod
    def _normalize_quat(q):
        norm = math.sqrt(sum(x*x for x in q))
        if norm == 0: return q
        return [x/norm for x in q]

    @staticmethod
    def _quat_to_euler(q):
        q0, q1, q2, q3 = q
        sinr_cosp = 2.0*(q0*q1 + q2*q3)
        cosr_cosp = 1.0 - 2.0*(q1*q1 + q2*q2)
        roll = math.atan2(sinr_cosp, cosr_cosp)
        sinp = 2.0*(q0*q2 - q3*q1)
        pitch = math.copysign(math.pi/2, sinp) if abs(sinp) >= 1 else math.asin(sinp)
        siny_cosp = 2.0*(q0*q3 + q1*q2)
        cosy_cosp = 1.0 - 2.0*(q2*q2 + q3*q3)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        return roll, pitch, yaw

    # ---------------- Properties for alpha / ODR ----------------
    @property
    def alpha(self): return self._alpha
    @alpha.setter
    def alpha(self, value): self._alpha = value

    @property
    def accel_rate(self): return self._accel_rate
    @accel_rate.setter
    def accel_rate(self, value):
        self._accel_rate = value
        self.sensor.accelerometer_data_rate = value

    @property
    def gyro_rate(self): return self._gyro_rate
    @gyro_rate.setter
    def gyro_rate(self, value):
        self._gyro_rate = value
        self.sensor.gyro_data_rate = value

