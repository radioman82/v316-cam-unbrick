"""App neu starten, Log leeren, serielle Ausgabe mitschneiden.

usage: python restart_watch.py [sekunden]
"""
import serial, time, sys

secs = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0

s = serial.Serial("COM11", 115200, timeout=1)


def send(cmd, wait=0.6):
    s.reset_input_buffer()
    s.write(cmd.encode() + b"\n")
    time.sleep(wait)
    out = b""
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.05)
    return out.decode("utf-8", errors="replace")


send("killall -9 sdvcam 2>/dev/null", 1.2)
send("umount /usr/bin/sdvcam 2>/dev/null")
send("mount --bind /mnt/extsd/sdvcam /usr/bin/sdvcam")
send("mount --bind /mnt/extsd/custom_ui /usr/share/minigui/res/images")
send("rm -f /tmp/log/LOG-SDV-* /tmp/as_done /tmp/AS /tmp/A /tmp/B /tmp/OL_OK /tmp/OL_NULL", 0.8)
send("sync", 0.8)

s.reset_input_buffer()
s.write(b"/usr/bin/sdvcam &\n")
t0 = time.time()
buf = b""
while time.time() - t0 < secs:
    buf += s.read(4096)
print(buf.decode("utf-8", errors="replace")[-4000:])
print("=" * 60)
print(send("ps | grep sdvcam | grep -v grep", 1.0))
print(send("ls -la /tmp/as_done /tmp/OL_OK /tmp/OL_NULL 2>/dev/null", 0.8))
s.close()
