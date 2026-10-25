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

print("--- TOOLS ---")
print(run("which i2cget; which i2cdump; which axp"))
print("--- PMU SYSFS ATTRS ---")
print(run("ls -la /sys/devices/platform/soc/pmu0/"))
print(run("find /sys -name '*reg*' 2>/dev/null | grep pmu"))
s.close()
