import serial, time

s = serial.Serial('COM11', 115200, timeout=2)
def run(cmd):
    s.write(cmd.encode() + b'\n')
    time.sleep(0.3)
    out = b''
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.1)
    return out.decode('utf-8', errors='replace')

print("Stopping previous...")
run('killall -9 sdvcam 2>/dev/null')
time.sleep(1)
run('umount /usr/bin/sdvcam 2>/dev/null')
run('umount /usr/share/minigui/res/images 2>/dev/null')

print("Starting /etc/init.d/S01app start...")
print(run('/etc/init.d/S01app start'))
time.sleep(4)

print("Checking mounts:")
print(run('mount'))

print("Checking process:")
print(run('ps | grep sdvcam'))

s.close()
