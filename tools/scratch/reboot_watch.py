"""Kamera neu booten und den kompletten Bootvorgang mitschneiden.

usage: python reboot_watch.py [sekunden]
"""
import serial, time, sys

secs = float(sys.argv[1]) if len(sys.argv) > 1 else 75.0

s = serial.Serial("COM11", 115200, timeout=1)

s.reset_input_buffer()
s.write(b"sync; sync; reboot\n")
t0 = time.time()
buf = b""
while time.time() - t0 < secs:
    buf += s.read(4096)
s.close()

text = buf.decode("utf-8", errors="replace")
print(f"=== {len(text)} Zeichen empfangen ===")
# nur die interessanten Zeilen zeigen
keys = ("preview.cpp", "function_select", "sdvcam", "HandleMessage",
        "MSG_", "boot", "Mount", "mount", "login", "#", "EXT4", "mmc")
lines = [ln for ln in text.splitlines() if any(k in ln for k in keys)]
print("\n".join(lines[-60:]))
print("=== Ende ===")
