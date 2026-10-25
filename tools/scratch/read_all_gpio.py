import serial, time

s = serial.Serial('COM11', 115200, timeout=2)
def run(cmd):
    s.write(cmd.encode() + b'\n')
    time.sleep(0.3)
    out = b''
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.05)
    return out.decode('utf-8', errors='replace')

print("--- READ ALL GPIO DATA REGISTERS ---")
for port, offset in [('PA', 0x10), ('PB', 0x34), ('PC', 0x58), ('PD', 0x7c), ('PE', 0xa0), ('PF', 0xc4), ('PG', 0xe8), ('PH', 0x10c)]:
    addr = 0x0300b000 + offset
    val = run(f"devmem {hex(addr)} 32").strip()
    print(f"Port {port} ({hex(addr)}): {val}")

# Also R_PIO (Port L) at 0x07022000
addr_pl = 0x07022000 + 0x10
val_pl = run(f"devmem {hex(addr_pl)} 32").strip()
print(f"Port PL ({hex(addr_pl)}): {val_pl}")

s.close()
