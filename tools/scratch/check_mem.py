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

print("--- DEVMEM TEST ---")
print(run("which devmem; devmem 0x0300b000 32 2>/dev/null"))
print("--- SUNXI DUMP TEST ---")
print(run("cat /sys/class/sunxi_dump/dump 2>/dev/null; ls -l /sys/class/sunxi_dump/ 2>/dev/null"))
s.close()
