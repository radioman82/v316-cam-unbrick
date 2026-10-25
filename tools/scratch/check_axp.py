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

print("--- AXP SYSFS / DRIVER ---")
print(run("find /sys -name '*axp*' 2>/dev/null; find /sys -name '*pmu*' 2>/dev/null"))
print("--- I2C DEVICES ---")
print(run("ls -l /sys/bus/i2c/devices/"))
print("--- DMESG AXP ---")
print(run("dmesg | grep -i -e axp -e pmu -e powerkey"))
s.close()
