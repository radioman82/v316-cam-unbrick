import serial, time

s = serial.Serial('COM11', 115200, timeout=1)

def run(cmd):
    s.write(cmd.encode() + b'\n')
    time.sleep(0.2)
    out = b''
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.05)
    return out.decode('utf-8', errors='replace')

# Clean up any leftover background cat
run("killall cat 2>/dev/null")
run("rm -f /tmp/ev1_test")

# Run cat /dev/input/event1 in background writing to /tmp/ev1_test
run("cat /dev/input/event1 > /tmp/ev1_test &")
print("Ready to capture on /dev/input/event1 (axp22x-powerkey)!")
s.close()
