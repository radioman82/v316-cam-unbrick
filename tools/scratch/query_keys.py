import serial, time

s = serial.Serial('COM11', 115200, timeout=1)

def run(cmd):
    s.write(cmd.encode() + b'\n')
    time.sleep(0.3)
    out = b''
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.05)
    return out.decode('utf-8', errors='replace')

print("--- DMESG INPUT DEVICES ---")
print(run("dmesg | grep -i -e input -e gpadc -e powerkey -e gpiokey"))
print("--- ALL KEYS IN INPUT/ ---")
print(run("ls -la /sys/class/input/"))
print("--- EVENT DEVICE PROPERTIES ---")
for ev in ['event0', 'event1', 'event2', 'event3']:
    print(f"=== {ev} ===")
    print(run(f"cat /sys/class/input/{ev}/device/name"))


s.close()
