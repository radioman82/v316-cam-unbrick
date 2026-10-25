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

# Replace '/usr/bin/sdvcam &' with '/usr/bin/sdvcam > /tmp/sdvcam.log 2>&1 &' in S01app
run("sed -i 's|/usr/bin/sdvcam &|/usr/bin/sdvcam > /tmp/sdvcam.log 2>\&1 \&|g' /etc/init.d/S01app")
run("sync")
print("Updated S01app:")
print(run("grep sdvcam /etc/init.d/S01app"))

print("Restarting S01app with logging...")
run("killall -9 sdvcam 2>/dev/null")
time.sleep(1)
run("umount /usr/bin/sdvcam 2>/dev/null")
run("umount /usr/share/minigui/res/images 2>/dev/null")
run("/etc/init.d/S01app start")
time.sleep(3)

print("Checking log head:")
print(run("head -n 30 /tmp/sdvcam.log"))

s.close()
