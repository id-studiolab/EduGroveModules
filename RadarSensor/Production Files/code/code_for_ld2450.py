import board
import busio
import ld2450  # Assuming you saved the code as ld2450.py

uart = busio.UART(board.TX, board.RX, baudrate=256000)  # Adjust pins and baudrate as needed

while True:
    parsed_data = ld2450.parse_ld2450_data(uart)  # Pass the uart object
    for target in parsed_data.targets:
        print(f"Target at ({target['x']}, {target['y']}) moving at {target['speed']} cm/s")
