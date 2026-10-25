import serial, time

ser = serial.Serial('COM11', 115200, timeout=1)
for reg in ['0x40', '0x41', '0x42', '0x43', '0x44', '0x48', '0x49', '0x4a', '0x4b', '0x4c', '0x4d']:
    ser.write(f'echo {reg} > /sys/class/axp/axp_reg; cat /sys/class/axp/axp_reg\n'.encode())
    time.sleep(0.1)

time.sleep(0.5)
out = ser.read(ser.in_waiting or 4000)
print(out.decode('utf-8', errors='replace'))
ser.close()
