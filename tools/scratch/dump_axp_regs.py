import serial, time

ser = serial.Serial('COM11', 115200, timeout=0.1)

regs = {}
for r in range(0x00, 0x60):
    hex_r = f"0x{r:02x}"
    ser.write(f"echo {hex_r} > /sys/class/axp/axp_reg; cat /sys/class/axp/axp_reg\n".encode())
    time.sleep(0.05)
    out = ser.read(ser.in_waiting or 200).decode('utf-8', errors='replace')
    for line in out.splitlines():
        if f"REG[{hex_r}]=" in line or f"REG[{hex(r)}]=" in line:
            parts = line.split('=')
            if len(parts) == 2:
                regs[hex_r] = parts[1].strip()

print(f"Read {len(regs)} registers:")
for r in sorted(regs.keys()):
    print(f"  {r}: {regs[r]}")

ser.close()
