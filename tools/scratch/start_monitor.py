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

# Start a background script on the camera that monitors all 4 event devices and interrupts
script = """
cat /dev/input/event0 > /tmp/ev0 &
cat /dev/input/event1 > /tmp/ev1 &
cat /dev/input/event2 > /tmp/ev2 &
cat /dev/input/event3 > /tmp/ev3 &
"""
run("rm -f /tmp/ev0 /tmp/ev1 /tmp/ev2 /tmp/ev3")
run("killall cat 2>/dev/null")
run("cat /dev/input/event0 > /tmp/ev0 &")
run("cat /dev/input/event1 > /tmp/ev1 &")
run("cat /dev/input/event2 > /tmp/ev2 &")
run("cat /dev/input/event3 > /tmp/ev3 &")

print("Monitors started on /dev/input/event0, 1, 2, 3.")
print("Initial interrupts:")
print(run("cat /proc/interrupts | grep -E 'ok_key|sunxi-gpadc|axp22x'"))

s.close()
