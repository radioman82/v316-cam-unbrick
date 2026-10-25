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

print("--- DEVICETREE POWERKEY ---")
print(run("cd /sys/firmware/devicetree/base/soc@03000000/pmu@0/powerkey@0 && ls -la; hexdump -C status 2>/dev/null; hexdump -C compatible 2>/dev/null"))
s.close()
