import serial, time
s = serial.Serial('COM11', 115200, timeout=1)
s.write(b'grep -B 5 -A 5 "is hiden" /tmp/log/sdvcam.INFO | head -n 30\n')
time.sleep(0.5)
print(s.read_all().decode('utf-8', errors='replace'))
s.close()
