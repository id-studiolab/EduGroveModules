import struct

class LD2450Data:
    """Represents a single frame of data from the LD2450 sensor."""

    def __init__(self, raw_bytes):
        """Initializes the LD2450Data object by parsing the raw bytes."""

        # Check for valid header and end of frame bytes
        if not (raw_bytes[:2] == b'\xaa\xff' and raw_bytes[-2:] == b'\x55\xcc'):
            raise ValueError("Invalid LD2450 data frame")

        # Parse target information
        self.targets = []
        for i in range(3):  # Up to 3 targets
            offset = 4 + i * 8  # Start of target data
            if offset >= len(raw_bytes) - 2:  # Check if enough bytes for target
                break

            x, y, speed, distance_res = struct.unpack("<hhhH", raw_bytes[offset:offset + 8])

            # Convert coordinates and speed to appropriate units (mm and cm/s)
            x = x if x & 0x8000 == 0 else x - 2**16
            y = y if y & 0x8000 == 0 else y - 2**15
            speed = speed if speed & 0x8000 == 0 else speed - 2**16

            self.targets.append({
                "x": x,
                "y": y,
                "speed": speed / 10.0,  # Convert to cm/s
                "distance_res": distance_res
            })

def parse_ld2450_data(raw_bytes):
    """Parses raw bytes from the LD2450 sensor and returns an LD2450Data object."""
    return LD2450Data(raw_bytes)
