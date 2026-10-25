import serial
import time

ser = serial.Serial('COM11', 115200, timeout=1.0)
ser.reset_input_buffer()
cmd = "tail -n 35 /tmp/log/sdvcam.INFO\n"
ser.write(cmd.encode('utf-8'))
time.sleep(0.5)
out = b''
for _ in range(25):
    if ser.in_waiting:
        out += ser.read(ser.in_waiting)
        time.sleep(0.05)
    else:
        time.sleep(0.05)
ser.close()
for l in out.decode('utf-8', errors='replace').splitlines():
    print(l)
