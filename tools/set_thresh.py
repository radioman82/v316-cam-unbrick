"""Set __mg_key_longpress_time in the running sdvcam and start a power logger.

usage: python set_thresh.py [ms]        (default 700)

Writes 4 bytes into /proc/<pid>/mem at 0x35f9c0 (= 3537344).
Nothing is written to flash; restarting the app restores 100 ms.
"""
import serial, sys, time

PORT = "COM11"
ADDR = 3537344
VAL = int(sys.argv[1]) if len(sys.argv) > 1 else 700

s = serial.Serial(PORT, 115200, timeout=3)


def run(cmd, w=2.0):
    s.reset_input_buffer()
    s.write(cmd.encode() + b"\n")
    time.sleep(w)
    out = b""
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.08)
    return out.decode("utf-8", errors="replace")


# --- pid of the running app ---------------------------------------------
pid = ""
for line in run("pidof sdvcam").splitlines():
    line = line.strip()
    if line.isdigit():
        pid = line
if not pid:
    print("FEHLER: sdvcam laeuft nicht")
    sys.exit(1)
print("PID =", pid)

# --- write the new threshold --------------------------------------------
raw = VAL.to_bytes(4, "little")
octal = "".join("\\%03o" % b for b in raw)
cmd = "printf '%s' | dd of=/proc/%s/mem bs=1 seek=%d count=4 2>&1 | tail -1" % (
    octal, pid, ADDR)
print("schreibe:", cmd)
print(run(cmd, 2.0).strip())

# --- read back -----------------------------------------------------------
back = run("dd if=/proc/%s/mem bs=1 skip=%d count=4 2>/dev/null | od -An -tu4"
           % (pid, ADDR), 2.0)
print("rueckgelesen:", " ".join(back.split()))

# --- power logger on SD (survives power-off) ----------------------------
log = (
    ': > /mnt/extsd/dbg/pwr.log; '
    '(while true; do '
    'echo "$(cut -d\' \' -f1 /proc/uptime) '
    '$(cat /sys/class/power_supply/battery/status 2>/dev/null) '
    '$(cat /sys/class/power_supply/battery/capacity 2>/dev/null) '
    '$(cat /sys/class/power_supply/battery/current_now 2>/dev/null) '
    '$(cat /sys/class/power_supply/usb/online 2>/dev/null)" '
    '>> /mnt/extsd/dbg/pwr.log; sleep 5; done) &'
)
run(log, 1.5)
time.sleep(6)
print("--- pwr.log ---")
print(run("head -4 /mnt/extsd/dbg/pwr.log", 2.0))
s.close()
