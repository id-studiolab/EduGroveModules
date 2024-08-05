import time
import board
import busio
import struct

# Define constants
CMD_HEAD = b'\xfd\xfc\xfb\xfa'
CMD_TAIL = b'\x04\x03\x02\x01'
REPORT_HEAD = b'\xf4\xf3\xf2\xf1'
REPORT_TAIL = b'\xf8\xf7\xf6\xf5'
REPORT_DATA_HEAD = b'\xaa'
REPORT_DATA_TAIL = b'\x55\x00'

ENABLE_CONFIG_CMD = 0xff
END_CONFIG_CMD = 0xfe
SET_MAX_CMD = 0x60
READ_PARAMETER_CMD = 0x61
ENABLE_ENGINEERING_CMD = 0x62
END_ENGINEERING_CMD = 0x63
SET_SENSITIVITY_CMD = 0x64
READ_FIRMWARE_VERSION_CMD = 0xa0
SET_BAUDRATE_CMD = 0xa1
FACTORY_RESET_CMD = 0xa2
RESTART_CMD = 0xa3

BAUDRATE_9600 = 1
BAUDRATE_19200 = 2
BAUDRATE_38400 = 3
BAUDRATE_57600 = 4
BAUDRATE_115200 = 5
BAUDRATE_230400 = 6
BAUDRATE_256000 = 7
BAUDRATE_460800 = 8

class LD2410:
    def __init__(self, uart):
        self.uart = uart
        self.buf = b''
        print("UART initialized.")

        self.target_state = 0
        self.moving_distance = 0
        self.moving_energy = 0
        self.stationary_distance = 0
        self.stationary_energy = 0
        self.detection_distance = 0

        self.max_moving_gate = 0
        self.max_stationary_gate = 0
        self.gate_moving_energy = [0] * 9
        self.gate_stationary_energy = [0] * 9

        self.ack_cmd = 0
        self.ack_data = b''

    def update(self):
        while self.uart.in_waiting > 0:
            self.buf += self.uart.read(1)
            #print("Received data:", self.buf)
            if len(self.buf) >= 10 and (self.buf[-4:] == CMD_TAIL or self.buf[-4:] == REPORT_TAIL):
                self._parse_buffer()

    def _parse_buffer(self):
        while True:
            if self.buf[:4] == CMD_HEAD:
                print("Parsing ACK...")
                self._parse_ack()
            elif self.buf[:4] == REPORT_HEAD:
                #print("Parsing report...")
                self._parse_report()
            if len(self.buf) < 10:
                break
            self.buf = self.buf[1:]

    def _parse_ack(self):
        if len(self.buf) < 8:
            return
        self.ack_cmd = self.buf[4]
        self.ack_data = self.buf[5:-4]
        print(f"ACK received: cmd={self.ack_cmd}, data={self.ack_data}")
        self.buf = b''

    def _parse_report(self):
        if len(self.buf) < 18:
            return
        report_len = struct.unpack('<H', self.buf[4:6])[0]
        if report_len != 13:
            return
        report_type = self.buf[6]
        if report_type == 0x02:
            self.target_state = self.buf[8]
            self.moving_distance = struct.unpack('<H', self.buf[9:11])[0]
            self.moving_energy = self.buf[11]
            self.stationary_distance = struct.unpack('<H', self.buf[12:14])[0]
            self.stationary_energy = self.buf[14]
            self.detection_distance = struct.unpack('<H', self.buf[15:17])[0]
            #print(f"Report parsed: target_state={self.target_state}, moving_distance={self.moving_distance}, moving_energy={self.moving_energy}, stationary_distance={self.stationary_distance}, stationary_energy={self.stationary_energy}, detection_distance={self.detection_distance}")
        self.buf = b''

    def send_command(self, cmd, data=b''):
        cmd_data_len = bytes([len(cmd) + len(data), 0x00])
        frame = CMD_HEAD + cmd_data_len + cmd + data + CMD_TAIL
        print("Sending command:", frame)
        self.uart.write(frame)

    def read_firmware_version(self):
        self.send_command(bytes([READ_FIRMWARE_VERSION_CMD]))
        time.sleep(0.1)
        if self.uart.in_waiting:
            response = self.uart.read(self.uart.in_waiting)
            if response[:4] == CMD_HEAD and response[-4:] == CMD_TAIL:
                if response[4] == READ_FIRMWARE_VERSION_CMD:
                    version_major = response[5]
                    version_minor = response[6]
                    print(f"Firmware version: {version_major}.{version_minor}")
                else:
                    print("Unexpected command in response.")
            else:
                print("Invalid firmware version response format.")
        else:
            print("No firmware version data received.")

    def factory_reset(self):
        self.send_command(bytes([FACTORY_RESET_CMD]))
        print("Factory reset command sent.")

    def restart(self):
        self.send_command(bytes([RESTART_CMD]))
        print("Restart command sent.")

    def set_sensitivity(self, level):
        self.send_command(bytes([SET_SENSITIVITY_CMD, level]))
        # Additional handling for setting sensitivity

    # Additional methods for other functionalities
