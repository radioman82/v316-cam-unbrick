import serial
import time
import sys
import os

LOG_FILE = "d:/v316cm/live_key_presses.log"
PORT = "COM11"
BAUD = 115200

def log_msg(msg):
    timestamp = time.strftime("[%H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def main():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)
    except Exception as e:
        print(f"Fehler beim Öffnen von {PORT}: {e}", flush=True)
        return

    log_msg("=== DAUERHAFTES TASTEN-LOGGING GESTARTET ===")
    log_msg(f"Logdatei wird geschrieben nach: {LOG_FILE}")
    log_msg("Überwacht: event0 (ADC/Seitentasten), event1 (Powerkey), event2 (OK/Shutter), event3 (IR) & sdvcam.INFO")

    # Clear buffers
    ser.write(b'\x03\n\x03\n')
    time.sleep(0.2)
    ser.reset_input_buffer()

    # Launch background tail on target
    setup_cmd = (
        "killall tail 2>/dev/null; "
        "tail -f /tmp/log/sdvcam.INFO 2>/dev/null &\n"
    )
    ser.write(setup_cmd.encode())
    time.sleep(0.3)

    last_irq_check = time.time()
    last_irqs = {}

    def fetch_irqs():
        ser.write(b"\ncat /proc/interrupts | grep -e ok_key -e axp22x -e gpioir_EINT\n")
        time.sleep(0.12)
        raw = ser.read_all().decode('utf-8', errors='ignore')
        res = {}
        for l in raw.splitlines():
            if 'ok_key' in l:
                p = l.split()
                if len(p) > 1 and p[1].isdigit(): res['ok_key (OK-Taste)'] = int(p[1])
            if 'axp22x' in l:
                p = l.split()
                if len(p) > 1 and p[1].isdigit(): res['axp22x (Power-Chip)'] = int(p[1])
            if 'gpioir_EINT' in l:
                p = l.split()
                if len(p) > 1 and p[1].isdigit(): res['gpioir_EINT'] = int(p[1])
        return res

    last_irqs = fetch_irqs()
    log_msg(f"Initiale Hardware-Interrupts: {last_irqs}")
    log_msg(">> BEREIT. Bitte drücke jetzt beliebige Tasten an der Kamera...")

    try:
        while True:
            # Read serial app logs
            if ser.in_waiting:
                chunk = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                for line in chunk.splitlines():
                    line = line.strip()
                    if not line or line.startswith('/ #'):
                        continue
                    # Match button/key logs
                    if 'keycode' in line.lower():
                        log_msg(f"*** [TASTE REGISTRIERT]: {line}")
                    elif any(k in line.lower() for k in ['msg_keydown', 'msg_keyup', 'keyproc', 'play key tone', 'left key', 'ok_key']):
                        log_msg(f"  [APP-EVENT]: {line}")
                    elif 'msg: 85' in line:
                        log_msg(f"  [MODUSWECHSEL]: {line}")

            # Check hardware interrupts
            if time.time() - last_irq_check > 1.0:
                cur_irqs = fetch_irqs()
                for k in cur_irqs:
                    if k in last_irqs and cur_irqs[k] != last_irqs[k]:
                        diff = cur_irqs[k] - last_irqs[k]
                        log_msg(f"[HARDWARE-INTERRUPT]: {k} ausgelöst! (+{diff} Impulse, Neu: {cur_irqs[k]})")
                        last_irqs[k] = cur_irqs[k]
                last_irq_check = time.time()

            time.sleep(0.04)

    except KeyboardInterrupt:
        log_msg("Logging beendet.")
    finally:
        ser.write(b'\x03killall tail 2>/dev/null\n')
        time.sleep(0.2)
        ser.close()

if __name__ == '__main__':
    main()
