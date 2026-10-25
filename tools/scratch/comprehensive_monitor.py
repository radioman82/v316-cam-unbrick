import serial, time

ser = serial.Serial('COM11', 115200, timeout=0.1)

print("=== LIVE MONITORING GESTARTET (45 Sekunden) ===")
print("Bitte jetzt drücken: kurz, 1s, 2s...")

# Start evtest-like or hexdump on all event devices in background on camera
ser.write(b"hexdump /dev/input/event0 > /tmp/ev0.hex 2>&1 &\n")
ser.write(b"hexdump /dev/input/event1 > /tmp/ev1.hex 2>&1 &\n")
ser.write(b"hexdump /dev/input/event2 > /tmp/ev2.hex 2>&1 &\n")
time.sleep(0.2)

t0 = time.time()
found_any = False
while time.time() - t0 < 45:
    # Check AXP 0x4A
    ser.write(b"echo 0x4a > /sys/class/axp/axp_reg; cat /sys/class/axp/axp_reg\n")
    time.sleep(0.3)
    out = ser.read(ser.in_waiting or 200).decode('utf-8', errors='replace')
    for line in out.splitlines():
        if "REG[0x4a]=" in line:
            val = line.split("=")[1].strip()
            if val not in ("0x0", "0x00"):
                print(f"[{time.strftime('%H:%M:%S')}] AXP REG 0x4A: {val}")
                found_any = True

# Check event dumps
ser.write(b"killall hexdump; ls -l /tmp/ev*.hex; head -n 5 /tmp/ev*.hex\n")
time.sleep(0.5)
out = ser.read(ser.in_waiting or 2000).decode('utf-8', errors='replace')
print("--- Event Hex Dumps ---")
print(out)

# Check interrupts
ser.write(b"cat /proc/interrupts | grep -E 'ok_key|axp22x|sunxi-gpadc'\n")
time.sleep(0.5)
out2 = ser.read(ser.in_waiting or 2000).decode('utf-8', errors='replace')
print("--- Interrupts ---")
print(out2)

ser.close()
