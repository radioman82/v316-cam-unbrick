import serial
import time

ser = serial.Serial('COM11', 115200, timeout=1.0)
ser.reset_input_buffer()

# Disable S50usb temporarily and reboot to test if camera boots cleanly into viewfinder!
cmd = """mv /etc/init.d/S50usb /etc/init.d/K50usb
sync
reboot
"""
ser.write(cmd.encode('utf-8'))
time.sleep(1.0)
ser.close()
print("Disabled S50usb and rebooted camera! Waiting for boot...")
