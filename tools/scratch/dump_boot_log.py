import serial, time
s = serial.Serial('COM11', 115200, timeout=1)
s.write(b'sed -n "481,550p" /tmp/log/sdvcam.INFO\n')
time.sleep(0.8)
print(s.read_all().decode('utf-8', errors='replace'))
s.close()
