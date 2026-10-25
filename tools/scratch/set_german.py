import serial
import time

ser = serial.Serial('COM11', 115200, timeout=1.0)
ser.reset_input_buffer()

# 1. Update setting.lua to German (language 6)
cmd_lang = "sed -i 's/\\[\"ml_device_language\"\\] = [0-9]/\\[\"ml_device_language\"\\] = 6/' /data/setting.lua; sync\n"
ser.write(cmd_lang.encode('utf-8'))
time.sleep(0.5)

# Verify
ser.write(b"grep ml_device_language /data/setting.lua\n")
time.sleep(0.5)
out = b''
for _ in range(15):
    if ser.in_waiting:
        out += ser.read(ser.in_waiting)
        time.sleep(0.05)
ser.close()
print("Language setting result:", out.decode('utf-8', errors='replace'))
