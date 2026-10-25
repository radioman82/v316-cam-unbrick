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

print("--- I2CDETECT BUS 0 ---")
print(run("/usr/sbin/i2cdetect -y 0 2>/dev/null || which i2cdetect"))
print("--- I2CDETECT BUS 1 ---")
print(run("/usr/sbin/i2cdetect -y 1 2>/dev/null"))
print("--- I2CDETECT BUS 2 ---")
print(run("/usr/sbin/i2cdetect -y 2 2>/dev/null"))
s.close()
