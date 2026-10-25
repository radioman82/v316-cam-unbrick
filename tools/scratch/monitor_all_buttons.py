import serial
import time
import sys

s = serial.Serial('COM11', 115200, timeout=0.1)

# Clear buffers
s.write(b'\x03\n\x03\n')
time.sleep(0.3)
s.reset_input_buffer()

print("="*70, flush=True)
print(">>> ULTRA-TASTEN-MONITOR GESTARTET <<<", flush=True)
print("Überwacht live:", flush=True)
print(" 1. sdvcam App-Logs (/tmp/log/sdvcam.INFO)", flush=True)
print(" 2. Hardware-Interrupts (ok_key, axp22x, gpadc)", flush=True)
print(" 3. Alle Linux Input-Events (event0, event1, event2)", flush=True)
print("="*70, flush=True)
print("BITTE JETZT DIE VORDERE TASTE DRÜCKEN (kurz und lang)!", flush=True)
print("Danach auch mal die Seitentasten und OK zum Vergleich drücken.", flush=True)
print("="*70, flush=True)

# Launch background logger on camera that pipes both event logs and sdvcam.INFO
cmd = (
    "killall tail 2>/dev/null; "
    "tail -f /tmp/log/sdvcam.INFO 2>/dev/null &\n"
)
s.write(cmd.encode())
time.sleep(0.3)

last_irq_check = time.time()
baseline_irq = {}

def get_irqs():
    s.write(b"\ncat /proc/interrupts | grep -e ok_key -e axp22x\n")
    time.sleep(0.1)
    res = s.read_all().decode('utf-8', errors='ignore')
    out = {}
    for line in res.splitlines():
        if 'ok_key' in line:
            parts = line.split()
            if len(parts) > 1 and parts[1].isdigit():
                out['ok_key'] = int(parts[1])
        if 'axp22x' in line:
            parts = line.split()
            if len(parts) > 1 and parts[1].isdigit():
                out['axp22x'] = int(parts[1])
    return out

baseline_irq = get_irqs()
print("Initiale Interrupt-Werte:", baseline_irq, flush=True)

try:
    while True:
        if s.in_waiting:
            chunk = s.read(s.in_waiting).decode('utf-8', errors='ignore')
            for line in chunk.splitlines():
                line = line.strip()
                if not line or line.startswith('/ #'):
                    continue
                # Filter for interesting button/gui events
                if any(k in line.lower() for k in ['key', 'msg', 'button', 'press', 'down', 'up', 'handle', 'postmsg']):
                    print(f"  [APP/TASTE]: {line}", flush=True)

        if time.time() - last_irq_check > 1.5:
            cur_irq = get_irqs()
            for k in cur_irq:
                if k in baseline_irq and cur_irq[k] != baseline_irq[k]:
                    diff = cur_irq[k] - baseline_irq[k]
                    print(f"\n>>> [INTERRUPT TRIGGER!] {k} hat ausgelöst! (+{diff} Impulse, Neu: {cur_irq[k]}) <<<\n", flush=True)
                    baseline_irq[k] = cur_irq[k]
            last_irq_check = time.time()

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nBeendet.", flush=True)
finally:
    s.write(b'\x03killall tail 2>/dev/null\n')
    time.sleep(0.2)
    s.close()
