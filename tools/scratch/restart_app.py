import serial, time

s = serial.Serial('COM11', 115200, timeout=1)
s.write(b'killall -9 webapp sdvcam 2>/dev/null\n')
time.sleep(1)
s.write(b'/etc/init.d/S01app start\n')
time.sleep(3)
s.write(b'ps | grep sdvcam\n')
time.sleep(0.5)
out = s.read(s.in_waiting or 2000).decode('utf-8', errors='ignore')
print(out)
s.close()
