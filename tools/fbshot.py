"""Framebuffer-Ausschnitt pixelgenau auslesen und als PNG rendern.

Liest einen rechteckigen Ausschnitt aus /dev/fb0 (320x480, 32bpp, stride 1280)
ueber die serielle Konsole (1 Zeichen pro Pixel, Schwellwert auf Helligkeit)
und schreibt daraus ein PNG. So laesst sich der Bildschirm kontrollieren,
ohne am Geraet abzulesen.

usage: python fbshot.py [--y0 0] [--y1 120] [--x0 0] [--x1 320]
                        [--scale 3] [--out screen.png]
"""
import argparse
import struct
import sys
import time
import zlib

import serial

REMOTE = r"""
dd if=/dev/fb0 bs=1280 skip=%(y0)d count=%(n)d 2>/dev/null | od -An -tu1 -v -w1280 | awk -v x0=%(b0)d -v x1=%(b1)d '{s="";for(i=x0;i<=x1;i+=4){if($i>100)s=s"#";else s=s"."}print s}'
echo FBEND
"""


def write_png(path, width, height, rows, scale):
    """rows: Liste von Strings mit '#'/'.' (width Zeichen)."""
    w = width * scale
    h = height * scale
    raw = bytearray()
    for r in rows:
        line = bytearray()
        for ch in r:
            v = 255 if ch == "#" else 0
            line += bytes((v, v, v)) * scale   # jeden Pixel skalieren
        for _ in range(scale):
            raw += b"\x00" + line

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def grab(ser, y0, n, x0, x1, timeout=30.0):
    script = REMOTE % {"y0": y0, "n": n, "b0": x0 * 4 + 1, "b1": x1 * 4 + 1}
    ser.reset_input_buffer()
    ser.write(("cat > /tmp/fb2.sh <<'XEOF'\n" + script + "XEOF\nsh /tmp/fb2.sh\n").encode())
    buf = b""
    t0 = time.time()
    seen = None
    ser.timeout = 0.2
    while time.time() - t0 < timeout:
        n = ser.in_waiting
        if n:
            buf += ser.read(n)
        else:
            b = ser.read(1)          # blockiert kurz statt zu schlafen
            if b:
                buf += b
        if b"FBEND" in buf and seen is None:
            seen = time.time()
        if seen and time.time() - seen > 1.0:
            break
    text = buf.decode("utf-8", errors="replace")
    return [ln for ln in text.splitlines()
            if ln and set(ln) <= set("#.") and len(ln) >= (x1 - x0)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="COM11")
    ap.add_argument("--y0", type=int, default=0)
    ap.add_argument("--y1", type=int, default=120)
    ap.add_argument("--x0", type=int, default=0)
    ap.add_argument("--x1", type=int, default=319)
    ap.add_argument("--scale", type=int, default=3)
    ap.add_argument("--chunk", type=int, default=40)
    ap.add_argument("--out", default="screen.png")
    a = ap.parse_args()

    ser = serial.Serial(a.port, 115200, timeout=3)
    time.sleep(0.2)

    rows = []
    y = a.y0
    while y < a.y1:
        n = min(a.chunk, a.y1 - y)
        part = []
        for attempt in range(3):
            part = grab(ser, y, n, a.x0, a.x1)
            if len(part) >= n:
                break
            print(f"  Block y={y}: {len(part)}/{n}, Versuch {attempt + 2}")
        rows.extend(part[:n])
        y += n
    ser.close()

    want = a.y1 - a.y0
    if len(rows) < want:
        print(f"WARNUNG: {len(rows)} von {want} Zeilen")
    if not rows:
        print("Kein Bild erhalten.")
        return 1
    write_png(a.out, len(rows[0]), len(rows), rows, a.scale)
    print(f"{a.out}: {len(rows[0])}x{len(rows)} Pixel, {a.scale}x skaliert")
    return 0


if __name__ == "__main__":
    sys.exit(main())
