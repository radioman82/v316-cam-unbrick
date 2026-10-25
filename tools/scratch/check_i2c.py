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

print("--- 0-0010 ---")
print(run("ls -l /sys/bus/i2c/devices/0-0010/; cat /sys/bus/i2c/devices/0-0010/name"))
print("--- 1-0038 ---")
print(run("cat /sys/bus/i2c/devices/1-0038/name 2>/dev/null"))
print("--- 2-0068 ---")
print(run("cat /sys/bus/i2c/devices/2-0068/name 2>/dev/null"))
s.close()
