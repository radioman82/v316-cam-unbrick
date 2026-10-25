import serial
import time
import sys

def main():
    try:
        ser = serial.Serial('COM11', 115200, timeout=0.1)
    except Exception as e:
        print(f"Error opening COM11: {e}")
        return

    print("COM11 verbunden!")
    
    # Interrupt any running process and clear buffer
    ser.write(b'\x03\n\x03\n')
    time.sleep(0.3)
    ser.reset_input_buffer()
    
    # Launch hexdump monitors for each input event + tail sdvcam.INFO
    setup_cmd = (
        "killall hexdump tail 2>/dev/null; "
        "hexdump -v /dev/input/event0 2>/dev/null & "
        "hexdump -v /dev/input/event1 2>/dev/null & "
        "hexdump -v /dev/input/event2 2>/dev/null & "
        "tail -f /tmp/log/sdvcam.INFO 2>/dev/null &\n"
    )
    ser.write(setup_cmd.encode('utf-8'))
    time.sleep(0.5)

    print("\n" + "="*65)
    print(">>> *** TASTEN-TEST GESTARTET (25 Sekunden) *** <<<")
    print("Bitte druecke JETZT nacheinander jede Taste an der Kamera:")
    print(" -> 1. Power / Mode")
    print(" -> 2. Shutter (Ausloeser oben)")
    print(" -> 3. Pfeil nach oben (Seite)")
    print(" -> 4. Pfeil nach unten / WiFi (Seite)")
    print("="*65 + "\n", flush=True)

    start = time.time()
    last_tick = time.time()
    events = []
    
    while time.time() - start < 25.0:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if line and not line.startswith('/ #'):
                if any(x in line for x in ['00000', '00001', '00002', '00003']) or any(k in line.lower() for k in ['key', 'msg', 'event', 'down', 'up', 'button']):
                    print(f"  [TASTE ERKANNT]: {line}", flush=True)
                    events.append(line)
        time.sleep(0.01)
        if time.time() - last_tick > 4.0:
            rem = int(20 - (time.time() - start))
            print(f"... noch {rem} Sekunden Testzeit ...", flush=True)
            last_tick = time.time()

    # Clean up background monitors
    ser.write(b'\x03\nkillall hexdump tail 2>/dev/null\n')
    time.sleep(0.4)
    ser.close()
    
    print("\n" + "="*65)
    print("--- TEST BEENDET. ---")
    print(f"Insgesamt empfangene Signale: {len(events)}")
    print("="*65)

if __name__ == '__main__':
    main()
