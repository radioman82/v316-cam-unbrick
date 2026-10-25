import serial
import time
import sys

PORT = "COM11"
BAUD = 115200

s = serial.Serial(PORT, BAUD, timeout=0.1)

def run(cmd):
    s.write(cmd.encode() + b'\n')
    time.sleep(0.08)
    out = b''
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.01)
    return out.decode('utf-8', errors='replace')

# Clear buffers
s.write(b'\x03\n\x03\n')
time.sleep(0.2)
s.reset_input_buffer()

print("="*70, flush=True)
print(">>> EXKLUSIVER MONITOR: NUR VORDERTASTE <<<", flush=True)
print("Überwacht alle 3 möglichen Hardware-Kanäle der Fronttaste:", flush=True)
print("  Kanal A: AXP22x Powerkey (/dev/input/event1 & IRQ 324)", flush=True)
print("  Kanal B: GPADC Widerstandsleiter (/dev/input/event0 & Channel 0)", flush=True)
print("  Kanal C: Alle Allwinner GPIO-Pins (PA, PB, PC, PD, PE, PF, PG, PH, PL)", flush=True)
print("="*70, flush=True)
print("BITTE JETZT DIE VORDERTASTE DRÜCKEN / KONTROLLIEREN / ÜBERBRÜCKEN!", flush=True)
print("="*70 + "\n", flush=True)

# Start background monitors for event0 and event1
run("killall hexdump tail 2>/dev/null; "
    "hexdump -v /dev/input/event1 2>/dev/null & "
    "tail -f /tmp/log/sdvcam.INFO 2>/dev/null &\n")

ports = [
    ('PA', 0x0300b010),
    ('PB', 0x0300b034),
    ('PC', 0x0300b058),
    ('PD', 0x0300b07c),
    ('PE', 0x0300b0a0),
    ('PF', 0x0300b0c4),
    ('PG', 0x0300b0e8),
    ('PH', 0x0300b10c),
    ('PL', 0x07022010),
]

def read_gpios():
    vals = {}
    for name, addr in ports:
        out = run(f"devmem {hex(addr)} 32")
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("0x"):
                try: vals[name] = int(line, 16)
                except: pass
    return vals

baseline_gpios = read_gpios()
print("Baseline GPIOs erfasst:", {k: hex(v) for k, v in baseline_gpios.items()}, flush=True)

last_check = time.time()
last_axp_irq = 0

try:
    while True:
        # Check incoming stream (hexdump on event1 + sdvcam.INFO)
        if s.in_waiting:
            chunk = s.read(s.in_waiting).decode('utf-8', errors='ignore')
            for line in chunk.splitlines():
                line = line.strip()
                if not line or line.startswith('/ #'):
                    continue
                if any(line.startswith(h) for h in ['00000', '00001']):
                    print(f"\n*** [EVENT1 / POWERKEY ERKANNT]: {line} ***", flush=True)
                elif any(k in line.lower() for k in ['power', 'keydown', 'keyup', 'left key', 'keyproc', '132', '136', 'msg: 85']):
                    print(f"  [APP/LOG]: {line}", flush=True)

        # Periodic hardware checks every 0.5s
        if time.time() - last_check > 0.5:
            # 1. Check AXP IRQ
            out_irq = run("cat /proc/interrupts | grep axp22x")
            for l in out_irq.splitlines():
                if 'axp22x' in l:
                    parts = l.split()
                    if len(parts) > 1 and parts[1].isdigit():
                        cnt = int(parts[1])
                        if cnt != last_axp_irq:
                            print(f"\n*** [AXP POWER-INTERRUPT TRIGGER!]: Count: {cnt} ***", flush=True)
                            last_axp_irq = cnt

            # 2. Check GPIOs for any bit toggle
            cur_gpios = read_gpios()
            for k in baseline_gpios:
                if k in cur_gpios and cur_gpios[k] != baseline_gpios[k]:
                    diff = cur_gpios[k] ^ baseline_gpios[k]
                    print(f"\n*** [GPIO PIN TRIGGER!] Port {k} geaendert: Mask {hex(diff)} (Neu: {hex(cur_gpios[k])}) ***", flush=True)
                    baseline_gpios[k] = cur_gpios[k]

            last_check = time.time()

        time.sleep(0.02)

except KeyboardInterrupt:
    print("\nMonitor gestoppt.", flush=True)
finally:
    s.write(b'\x03killall hexdump tail 2>/dev/null\n')
    time.sleep(0.2)
    s.close()
