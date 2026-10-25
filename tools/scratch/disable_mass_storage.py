import serial
import time

ser = serial.Serial('COM11', 115200, timeout=1.0)
ser.reset_input_buffer()

# In /etc/init.d/S50usb, comment out mass_storage.usb0
cmd = """sed -i 's|.*mass_storage.usb0.*|    # &|g' /etc/init.d/S50usb && sync
grep -i 'mass_storage' /etc/init.d/S50usb
"""
ser.write(cmd.encode('utf-8'))
time.sleep(1.0)
out = b''
for _ in range(25):
    if ser.in_waiting:
        out += ser.read(ser.in_waiting)
        time.sleep(0.05)
ser.close()
print("S50usb patched result:\n", out.decode('utf-8', errors='replace'))
