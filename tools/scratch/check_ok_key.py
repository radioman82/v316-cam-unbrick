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

print("--- OK_KEY DETAILS ---")
cmd = "cd /sys/firmware/devicetree/base/soc@03000000/gpiokey/ok_key && for f in *; do echo -n \"$f: \"; hexdump -C $f 2>/dev/null; done"
print(run(cmd))
s.close()
