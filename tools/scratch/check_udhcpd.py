import serial, time, sys

s = serial.Serial('COM11', 115200, timeout=1)
s.write(b"grep -v '^#' /etc/udhcpd.conf | grep '[a-zA-Z]'\n")
time.sleep(0.3)
raw = s.read(s.in_waiting or 4000)
sys.stdout.buffer.write(raw)
s.close()
