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

print("Restarting app via /etc/init.d/S01app start...")
run('killall -9 sdvcam 2>/dev/null')
time.sleep(1)
run('umount /usr/bin/sdvcam 2>/dev/null')
run('umount /usr/share/minigui/res/images 2>/dev/null')
run('/etc/init.d/S01app start')

print("Waiting 5 seconds for camera preview to initialize...")
time.sleep(5)

print("Checking log head:")
print(run('tail -n 20 /tmp/sdvcam.log'))

# Send KEY_VOLUMEUP (115 = 0x73) to /dev/input/event0
press = "\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x01\\x00\\x73\\x00\\x01\\x00\\x00\\x00"
syn   = "\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00"
rel   = "\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x01\\x00\\x73\\x00\\x00\\x00\\x00\\x00"

print("--- INJECTING SIDE UP (0x73 = 115) CLICK ---")
run(f'printf "{press}{syn}" > /dev/input/event0')
time.sleep(0.15)
run(f'printf "{rel}{syn}" > /dev/input/event0')
time.sleep(1.0)

print("--- LOG AFTER SIDE UP KEY ---")
print(run('tail -n 35 /tmp/sdvcam.log'))

s.close()
