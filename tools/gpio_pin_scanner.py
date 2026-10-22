import serial, time

s = serial.Serial('COM11', 115200, timeout=1)

def run(cmd):
    s.write(cmd.encode() + b'\n')
    time.sleep(0.05)
    out = b''
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.01)
    return out.decode('utf-8', errors='replace')

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

def read_all():
    vals = {}
    for name, addr in ports:
        out = run(f"devmem {hex(addr)} 32")
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("0x"):
                try:
                    vals[name] = int(line, 16)
                except:
                    pass
    return vals

baseline = read_all()
print("Baseline GPIO values captured:")
for k, v in baseline.items():
    print(f"  {k}: {hex(v)}")

print("\n--- GPIO SCANNER ACTIVE FOR 15 SECONDS ---")
print("BITTE JETZT DIE VORDERE TASTE MEHRFACH DRUECKEN UND HALTEN!")

t_end = time.time() + 15
changed_any = False

while time.time() < t_end:
    cur = read_all()
    for k in baseline:
        if k in cur and cur[k] != baseline[k]:
            diff = cur[k] ^ baseline[k]
            print(f"[GPIO TRIGGER!] {k} changed: was {hex(baseline[k])}, now {hex(cur[k])} (diff mask: {hex(diff)})")
            changed_any = True
            baseline[k] = cur[k]
    time.sleep(0.1)

if not changed_any:
    print("\nERGEBNIS: Kein einziger GPIO-Pin im gesamten Chip hat seinen Zustand geaendert.")
else:
    print("\nERGEBNIS: Pin-Aenderung gefunden!")

s.close()
