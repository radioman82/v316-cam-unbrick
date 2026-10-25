import serial, time

s = serial.Serial('COM11', 115200, timeout=2)
def run(cmd):
    s.write(cmd.encode() + b'\n')
    time.sleep(0.3)
    out = b''
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.05)
    return out.decode('utf-8', errors='replace')

print("--- FIND GPADC / ADC / KEY ---")
print(run("find /sys/ -name '*gpadc*' 2>/dev/null; find /sys/ -name '*key*' 2>/dev/null"))
s.close()
