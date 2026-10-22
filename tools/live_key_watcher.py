import serial, time

s = serial.Serial('COM11', 115200, timeout=1)

def run(cmd):
    s.write(cmd.encode() + b'\n')
    time.sleep(0.15)
    out = b''
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.02)
    return out.decode('utf-8', errors='replace')

print("Starting live watcher for 30 seconds...")

t_end = time.time() + 30
last_ev = ""
last_irq = ""

while time.time() < t_end:
    ev_stat = run("ls -l /tmp/ev*")
    irq_stat = run("grep -e ok_key -e sunxi-gpadc -e axp22x /proc/interrupts")
    
    if ev_stat != last_ev:
        print("\n[EVENT FILE CHANGE!]")
        print(ev_stat)
        last_ev = ev_stat

    if irq_stat != last_irq:
        print("\n[IRQ UPDATE]")
        print(irq_stat)
        last_irq = irq_stat
        
    time.sleep(0.5)

print("\n--- FINAL EVENT DUMP ---")
for f in ["/tmp/ev0", "/tmp/ev1", "/tmp/ev2", "/tmp/ev3"]:
    dump = run(f"hexdump -C {f} 2>/dev/null")
    print(f"Content of {f}:")
    print(dump)

s.close()
