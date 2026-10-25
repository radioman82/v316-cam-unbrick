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

print("Process md5:")
print(run('md5sum /proc/$(pidof sdvcam)/exe'))
print("Mounts:")
print(run('mount | grep mmc'))
s.close()
