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

print("--- OPEN INPUT FDS OF SDVCAM ---")
print(run("ls -l /proc/798/fd | grep event"))

s.close()
