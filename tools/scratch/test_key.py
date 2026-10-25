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

# Send KEY_VOLUMEUP (115 = 0x73) to /dev/input/event0
# On 32-bit Linux ARM: struct input_event is 16 bytes:
# tv_sec(4), tv_usec(4), type(2), code(2), value(4)
press = "\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x01\\x00\\x73\\x00\\x01\\x00\\x00\\x00"
syn   = "\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00"
rel   = "\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x01\\x00\\x73\\x00\\x00\\x00\\x00\\x00"

print("Injecting Side UP press...")
run(f'printf "{press}{syn}" > /dev/input/event0')
time.sleep(0.1)

print("Injecting Side UP release...")
run(f'printf "{rel}{syn}" > /dev/input/event0')
time.sleep(0.5)

print("Reading serial buffer...")
out = b''
t0 = time.time()
while time.time() - t0 < 1.5:
    if s.in_waiting:
        out += s.read(s.in_waiting)
    time.sleep(0.05)

print("Received:")
print(out.decode('utf-8', errors='replace'))

s.close()
