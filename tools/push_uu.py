"""Datei blockweise ueber die serielle Konsole auf die Kamera schieben.

Warum nicht einfach `cat > ziel <<EOF` mit Rohbytes: die serielle Konsole ist
ein tty in canonical mode. Rohbytes enthalten 0x03 (^C -> SIGINT), 0x04 (^D ->
EOF) und 0x13/0x11 (^S/^Q -> Flow-Control). Damit bricht der Transfer ab oder
haengt. uuencode benutzt nur Zeichen 0x20..0x5F und ist deshalb sicher.

usage: python push_uu.py <lokale_datei> <zielpfad_auf_kamera> [blockgroesse]
"""
import binascii
import os
import re
import serial
import sys
import time

src = sys.argv[1]
dst = sys.argv[2]
CHUNK = int(sys.argv[3]) if len(sys.argv) > 3 else 32768

TMP = "/mnt/extsd/dbg/up.uu"
PORT = "COM11"
BAUD = 115200
# 10 Bit pro Byte (8N1 + Start/Stop) -> ~11520 B/s Nutzdaten
BYTES_PER_SEC = BAUD / 10.0

data = open(src, "rb").read()
print("Quelle: %d Bytes" % len(data))

# uuencode (60 Zeichen pro Zeile, Standardformat)
body_lines = [binascii.b2a_uu(data[i:i + 45]) for i in range(0, len(data), 45)]
body = b"".join(body_lines)
uu = b"begin 644 " + os.path.basename(dst).encode() + b"\n" + body + b"end\n"
print("uuencode: %d Bytes (%.0f%% Aufschlag)" % (len(uu), 100.0 * len(uu) / len(data)))

# Bloecke an ZEILENGRENZEN schneiden: endet ein Block mitten in einer Zeile,
# landet der Heredoc-Terminator nicht am Zeilenanfang und die Shell haengt.
chunks = []
cur = []
size = 0
for ln in ([b"begin 644 " + os.path.basename(dst).encode() + b"\n"]
           + body_lines + [b"end\n"]):
    if size + len(ln) > CHUNK and cur:
        chunks.append(b"".join(cur))
        cur = []
        size = 0
    cur.append(ln)
    size += len(ln)
if cur:
    chunks.append(b"".join(cur))

s = serial.Serial(PORT, BAUD, timeout=3, write_timeout=90)
time.sleep(0.3)
s.reset_input_buffer()


def cmd(text, wait=1.2):
    s.reset_input_buffer()
    s.write(text.encode() + b"\n")
    time.sleep(wait)
    out = b""
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.05)
    return out.decode("utf-8", "replace")


def remote_size():
    # Marker benutzen: die Kommandozeile selbst wird vom tty zurueckgespiegelt
    # und enthaelt Ziffern, ein blosses Zahlen-Regex greift deshalb daneben.
    out = cmd("echo @@$(wc -c < %s)@@" % TMP, 1.0)
    m = re.search(r"@@\s*(\d+)\s*@@", out)
    return int(m.group(1)) if m else -1


print(cmd("rm -f %s; : > %s; echo START" % (TMP, TMP)))

sent = 0
block = 0
t0 = time.time()
total = len(uu)
for part in chunks:
    s.write(b"cat >> " + TMP.encode() + b" <<'UEOF'\n" + part + b"UEOF\n")
    # Sendezeit plus Reserve, damit der Empfaenger nicht ueberlaeuft
    time.sleep(len(part) / BYTES_PER_SEC + 0.6)
    sent += len(part)
    block += 1
    pct = 100.0 * sent / total
    print("  Block %3d  %6.1f%%  (%d/%d)" % (block, pct, sent, total), flush=True)

    if block % 4 == 0 or sent >= total:
        got = remote_size()
        if got != sent:
            print("!! ABBRUCH: Geraet hat %d Bytes, gesendet %d" % (got, sent))
            sys.exit(2)
        print("     Groesse ok: %d" % got, flush=True)

print("\nEntpacke ...")
print(cmd("uudecode -o %s %s; echo rc=$?" % (dst, TMP), 4.0))
print(cmd("wc -c %s; md5sum %s" % (dst, dst), 2.5))
print("Dauer: %.1f min" % ((time.time() - t0) / 60.0))
s.close()
