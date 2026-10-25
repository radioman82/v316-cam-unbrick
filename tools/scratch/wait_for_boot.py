import serial, time

ser = serial.Serial('COM11', 115200, timeout=0.1)
print("Dauerüberwachung aktiv (120s)... Warte auf Einschalten der Kamera.")

t0 = time.time()
while time.time() - t0 < 120:
    if ser.in_waiting:
        chunk = ser.read(ser.in_waiting)
        text = chunk.decode('utf-8', errors='replace')
        print(text, end='', flush=True)
        if 'sunxi#' in text:
            print("\n[U-Boot Prompt abgefangen -> boot wird gesendet!]\n")
            ser.write(b'\nboot\n')
        elif '/ #' in text:
            print("\n[Linux Shell aktiv und bereit!]\n")
            break
    time.sleep(0.05)

ser.close()
