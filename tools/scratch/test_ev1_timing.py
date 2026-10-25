import serial, time

ser = serial.Serial('COM11', 115200, timeout=0.1)

print("=== START TEST: SOFORT-TASTENTEST BEI BOOT ===")
# Start logging all events with millisecond timestamps
ser.write(b"killall evtest_logger 2>/dev/null\n")
time.sleep(0.1)

# Run a python one-liner on camera or shell loop to log event1
cmd = (
    "while true; do "
    "  hexdump -v -n 16 /dev/input/event1 | head -n 1 | "
    "  while read line; do echo \"[$(date +%s)] EV1: $line\"; done; "
    "done > /tmp/ev1_test.log 2>&1 &\n"
)
ser.write(cmd.encode())
time.sleep(0.5)

print("Logger laeuft auf der Kamera!")
print("Druecke jetzt die Vordertaste!")

t0 = time.time()
while time.time() - t0 < 10:
    ser.write(b"cat /tmp/ev1_test.log\n")
    time.sleep(1)
    out = ser.read(ser.in_waiting or 1000).decode('utf-8', errors='replace')
    if "EV1:" in out:
        print("Signal:", out.strip())
        break

ser.write(b"killall hexdump\n")
ser.close()
