"""Datei ueber die serielle Konsole auf die Kamera schieben (COM11).

Schickt ein quoting-freies Heredoc, damit Sonderzeichen unangetastet bleiben.

usage: python push_file.py <lokale_datei> <zielpfad_auf_kamera> [--exec]
"""
import serial, sys, time

src, dst = sys.argv[1], sys.argv[2]
make_exec = "--exec" in sys.argv

data = open(src, "rb").read()
if b"XEOF" in data:
    raise SystemExit("Datei enthaelt den Marker XEOF")

s = serial.Serial("COM11", 115200, timeout=3)
time.sleep(0.2)
s.reset_input_buffer()

payload = b"cat > " + dst.encode() + b" <<'XEOF'\n" + data + b"XEOF\n"
s.write(payload)
time.sleep(0.6 + len(data) / 900.0)

out = b""
while s.in_waiting:
    out += s.read(s.in_waiting)
    time.sleep(0.08)

if make_exec:
    s.write(("chmod 755 " + dst + "\n").encode())
    time.sleep(0.4)
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.05)

s.write(("wc -c " + dst + "; md5sum " + dst + "\n").encode())
time.sleep(0.8)
while s.in_waiting:
    out += s.read(s.in_waiting)
    time.sleep(0.05)
s.close()
print(out.decode("utf-8", errors="replace"))
