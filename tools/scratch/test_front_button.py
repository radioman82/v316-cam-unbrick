import serial
import time
import sys
import threading

PORT = 'COM11'
BAUD = 115200

def wait_for_shell(ser):
    print(f"Prüfe Verbindung zu {PORT}...", flush=True)
    ser.reset_input_buffer()
    
    # Try sending newline to see if shell is already there
    for _ in range(3):
        ser.write(b'\n')
        time.sleep(0.3)
        out = ser.read_all().decode('utf-8', errors='ignore')
        if '#' in out or '$' in out:
            print(">> Shell / Prompt auf Kamera ist aktiv!", flush=True)
            return True

    print("\n[BEREIT] Warte auf Boot der Kamera auf COM11 (Dauerüberwachung aktiv)...", flush=True)
    print(">> Bitte Strom/Akku anschließen oder Taster überbrücken zum Einschalten.", flush=True)
    
    boot_text = ""
    tick = time.time()
    while True:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            sys.stdout.write(chunk)
            sys.stdout.flush()
            boot_text += chunk
            if 'sunxi#' in chunk:
                print("\n[U-BOOT ERKANNT -> Starte Linux...]", flush=True)
                ser.write(b'\nboot\n')
                time.sleep(1)
            elif '#' in boot_text or 'login:' in boot_text or 'root@' in boot_text:
                time.sleep(0.5)
                ser.write(b'\n')
                print("\n>> Kamera hat gebootet und Shell ist bereit!", flush=True)
                return True
        time.sleep(0.05)

def main():
    print("=== TASTEN-TESTPROGRAMM AKTIV ===", flush=True)
    while True:
        try:
            print(f"Versuche {PORT} zu öffnen...", flush=True)
            ser = serial.Serial(PORT, BAUD, timeout=0.2)
            print(f">> {PORT} erfolgreich geöffnet!", flush=True)
            
            if wait_for_shell(ser):
                run_monitor(ser)
                break
            else:
                ser.close()
                time.sleep(1)
        except serial.SerialException as e:
            # Port not plugged in or disconnected
            time.sleep(1)
        except KeyboardInterrupt:
            print("\nAbbruch durch Benutzer.", flush=True)
            break
        except Exception as e:
            print(f"Unerwarteter Fehler: {e}", flush=True)
            time.sleep(1)

def run_monitor(ser):
    # Clear screen & interrupt any running jobs
    ser.write(b'\x03\n\x03\n')
    time.sleep(0.3)
    ser.reset_input_buffer()

    print("\n" + "="*70, flush=True)
    print(">>> INITIALISIERE TESTPROGRAMM AUF DER KAMERA <<<", flush=True)
    print("="*70, flush=True)

    # Check input events & interrupts baseline
    ser.write(b"killall hexdump tail 2>/dev/null; cat /proc/interrupts | grep -e axp -e gpadc -e ok_key -e gpio\n")
    time.sleep(0.5)
    baseline_irq = ser.read_all().decode('utf-8', errors='ignore')
    print("Initiale Interrupts:\n" + baseline_irq.strip(), flush=True)

    # Start hexdump on event0 (ADC/Keys), event1 (axp22x-powerkey), event2 (gpiokey)
    setup_cmd = (
        "hexdump -v /dev/input/event0 2>/dev/null & "
        "hexdump -v /dev/input/event1 2>/dev/null & "
        "hexdump -v /dev/input/event2 2>/dev/null & "
        "echo '=== MONITORE GESTARTET ==='\n"
    )
    ser.write(setup_cmd.encode('utf-8'))
    time.sleep(0.5)
    print(ser.read_all().decode('utf-8', errors='ignore'), flush=True)

    print("\n" + "#"*70, flush=True)
    print(">>> TESTPROGRAMM LÄUFT JETZT! <<<", flush=True)
    print("Bitte JETZT die vordere Taste drücken oder die Kontakte ÜBERBRÜCKEN!", flush=True)
    print("Überwachung aktiv für: event0, event1 (AXP Powerkey), event2 (GPIO).", flush=True)
    print("Drücke Strg+C zum Beenden.", flush=True)
    print("#"*70 + "\n", flush=True)

    try:
        last_poll = time.time()
        while True:
            if ser.in_waiting:
                chunk = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                for line in chunk.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('/ #'):
                        continue
                    # Check if line looks like hex dump from input event
                    if any(line.startswith(h) for h in ['000000', '000001', '000002', '000003', '000004']):
                        print(f"\n*** [TASTEN-SIGNAL ERKANNT!] ***", flush=True)
                        print(f"--> {line}\n", flush=True)
                    elif any(k in line.lower() for k in ['key', 'axp', 'power', 'press', 'down', 'up', 'button']):
                        print(f"--> [EVENT / LOG]: {line}", flush=True)
                    else:
                        print(f"    {line}", flush=True)

            # Periodically poll interrupts to see if hardware IRQ fired even without event
            if time.time() - last_poll > 3.0:
                ser.write(b"cat /proc/interrupts | grep -e axp -e gpadc -e ok_key\n")
                last_poll = time.time()

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nTest durch Benutzer abgebrochen.", flush=True)
    finally:
        ser.write(b'\x03\nkillall hexdump 2>/dev/null\n')
        time.sleep(0.3)
        ser.close()
        print("Testprogramm beendet und Bereinigung durchgeführt.", flush=True)

if __name__ == '__main__':
    main()
