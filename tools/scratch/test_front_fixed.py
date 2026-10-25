import serial, time

ser = serial.Serial('COM11', 115200, timeout=0.1)

# Check baseline interrupts
ser.write(b"cat /proc/interrupts | grep -e axp -e ok_key -e gpadc\n")
time.sleep(0.3)
print("Basis-Interrupts:")
print(ser.read(ser.in_waiting or 2000).decode('utf-8', errors='replace').strip())

# Start monitoring event1 and interrupts
ser.write(b"hexdump -v /dev/input/event1 > /tmp/front.hex &\n")
time.sleep(0.2)

print("\n" + "="*60)
print(">>> MONITOR LÄUFT FÜR 30 SEKUNDEN <<<")
print("Bitte JETZT die VORDERTASTE kurz drücken (1x kurz, 2x kurz)!")
print("="*60)

t0 = time.time()
while time.time() - t0 < 30:
    # Check AXP status
    ser.write(b"echo 0x4a > /sys/class/axp/axp_reg; cat /sys/class/axp/axp_reg\n")
    time.sleep(0.4)
    out = ser.read(ser.in_waiting or 200).decode('utf-8', errors='replace')
    for line in out.splitlines():
        if "REG[0x4a]=" in line:
            val = line.split("=")[1].strip()
            if val not in ("0x0", "0x00"):
                print(f"[{time.strftime('%H:%M:%S')}] AXP REG 0x4A: {val} !")

# Finish up
ser.write(b"killall hexdump; ls -l /tmp/front.hex; cat /tmp/front.hex\n")
time.sleep(0.5)
out = ser.read(ser.in_waiting or 2000).decode('utf-8', errors='replace')
print("\n--- Event1 (Powerkey) Hex Dump ---")
print(out)

ser.write(b"cat /proc/interrupts | grep -e axp -e ok_key -e gpadc\n")
time.sleep(0.3)
print("\n--- Interrupts nach dem Test ---")
print(ser.read(ser.in_waiting or 2000).decode('utf-8', errors='replace').strip())

ser.close()
