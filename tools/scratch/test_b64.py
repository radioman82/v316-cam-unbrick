import serial, time, sys

s = serial.Serial('COM11', 115200, timeout=1)
s.write(b'echo aGVsbG8= | base64 -d; echo "\nRET=$?"\n')
time.sleep(0.3)
raw = s.read(s.in_waiting or 4000)
sys.stdout.buffer.write(raw)
s.close()
