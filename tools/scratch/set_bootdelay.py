import serial, time

ser = serial.Serial('COM11', 115200, timeout=0.1)
print("=== WÄCHTER: SETZE BOOTDELAY AUF 1 SEKUNDE ===")
print("Bitte die Kamera jetzt einschalten (USB neu anstecken oder Fronttaste halten)!")

t0 = time.time()
caught_uboot = False

while time.time() - t0 < 60:
    if ser.in_waiting:
        chunk = ser.read(ser.in_waiting)
        text = chunk.decode('utf-8', errors='replace')
        print(text, end='', flush=True)
        
        # If autoboot prompt or U-Boot detected
        if 'Hit any key' in text or 'autoboot' in text or 'sunxi#' in text:
            caught_uboot = True
            print("\n[U-Boot Prompt abgefangen -> konfiguriere Bootdelay...]\n")
            ser.write(b'\n')
            time.sleep(0.2)
            ser.write(b'setenv bootdelay 1\n')
            time.sleep(0.3)
            ser.write(b'saveenv\n')
            time.sleep(0.5)
            ser.write(b'printenv bootdelay\n')
            time.sleep(0.3)
            ser.write(b'boot\n')
            break
    time.sleep(0.02)

# Read remaining boot messages
if caught_uboot:
    print("\nLese Boot-Meldungen...")
    t1 = time.time()
    while time.time() - t1 < 10:
        if ser.in_waiting:
            print(ser.read(ser.in_waiting).decode('utf-8', errors='replace'), end='', flush=True)
        time.sleep(0.05)

ser.close()
