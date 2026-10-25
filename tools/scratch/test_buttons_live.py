import serial, time

ser = serial.Serial('COM11', 115200, timeout=0.2)

# Clear any buffer
ser.read_all()

# Run a one-liner on target that monitors event0, 1, 2 and prints when anything happens
cmd = (
    "killall hexdump 2>/dev/null; "
    "hexdump -C /dev/input/event0 & "
    "hexdump -C /dev/input/event1 & "
    "hexdump -C /dev/input/event2 & "
    "echo READY_FOR_BUTTONS\n"
)
ser.write(cmd.encode())

print("Script running on camera, listening for 15 seconds...")
start = time.time()
while time.time() - start < 15:
    out = ser.read_all()
    if out:
        print(out.decode('utf-8', errors='ignore'), end='', flush=True)
    time.sleep(0.05)

ser.write(b"\x03killall hexdump 2>/dev/null\n")
time.sleep(0.5)
ser.close()
