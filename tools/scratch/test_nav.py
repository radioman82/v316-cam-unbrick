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

# Send KEY_VOLUMEDOWN (114 = 0x72) to /dev/input/event0
press = "\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x01\\x00\\x72\\x00\\x01\\x00\\x00\\x00"
syn   = "\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00"
rel   = "\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x01\\x00\\x72\\x00\\x00\\x00\\x00\\x00"

print("Injecting Side DOWN click...")
run(f'printf "{press}{syn}" > /dev/input/event0')
time.sleep(0.15)
run(f'printf "{rel}{syn}" > /dev/input/event0')
time.sleep(0.8)

print("Reading tail of /tmp/sdvcam.log:")
print(run('tail -n 25 /tmp/sdvcam.log'))
s.close()
