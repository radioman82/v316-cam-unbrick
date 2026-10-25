import serial, time

ser = serial.Serial('COM11', 115200, timeout=0.1)

print("Starte Polling von AXP REG 0x4A (Power Key Status) fuer 15 Sekunden...")
print("Bitte JETZT die VORDERTASTE kurz und lang druecken!")

t0 = time.time()
detected = []
while time.time() - t0 < 15:
    ser.write(b"echo 0x4a > /sys/class/axp/axp_reg; cat /sys/class/axp/axp_reg\n")
    time.sleep(0.3)
    out = ser.read(ser.in_waiting or 200).decode('utf-8', errors='replace')
    for line in out.splitlines():
        if "REG[0x4a]=" in line:
            val = line.split("=")[1].strip()
            if val != "0x0" and val != "0x00":
                detected.append((time.strftime("%H:%M:%S"), val))
                print(f"[{time.strftime('%H:%M:%S')}] AXP REG 0x4A AKTIVITÄT ENTDECKT: {val} !")

ser.close()
if detected:
    print(f"Ergebnis: {len(detected)} Events registriert: {detected}")
else:
    print("Ergebnis: Keine Änderung an REG 0x4A (immer 0x0).")
