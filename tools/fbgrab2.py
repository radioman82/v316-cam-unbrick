"""Framebuffer als ASCII holen - Zellmaximum statt Stichprobe (COM11).

Pro 8x16-Pixel-Zelle wird der groesste Blauwert genommen, damit duenne
Textstriche nicht durch das Raster fallen. 40x30 Zeichen.

usage: python fbgrab2.py [--wait N] [--from Y] [--to Y]
"""
import serial, time, sys

port = "COM11"
args = sys.argv[1:]


def opt(name, default):
    if name in args:
        return float(args[args.index(name) + 1])
    return default


wait = opt("--wait", 2.0)
y0 = int(opt("--from", 0))
y1 = int(opt("--to", 480))

AWK = (
    "{for(i=1;i<=1280;i+=4){p=int((i+3)/4);c=int((p-1)/8);"
    'if(c>39)c=39;if($i>m[c])m[c]=$i}}'
    'END{s="";for(c=0;c<40;c++){v=m[c]+0;k=int(v/26);'
    'if(k>9)k=9;s=s substr(" .:-=+*#%@",k+1,1)}print "|" s "|"}'
)

SCRIPT = (
    "cat > /tmp/mx.awk <<'AEOF'\n" + AWK + "\nAEOF\n"
    "y=" + str(y0) + "\n"
    "while [ $y -lt " + str(y1) + " ]; do\n"
    "  dd if=/dev/fb0 bs=1280 skip=$y count=1 2>/dev/null | "
    "od -An -tu1 -v -w1280 | awk -f /tmp/mx.awk\n"
    "  y=$((y+16))\n"
    "done\n"
    "echo FBEND\n"
)


def main():
    s = serial.Serial(port, 115200, timeout=3)
    time.sleep(0.2)
    s.reset_input_buffer()
    s.write(SCRIPT.encode())
    buf = b""
    t0 = time.time()
    seen_end = None
    while time.time() - t0 < 60:
        if s.in_waiting:
            buf += s.read(s.in_waiting)
            if b"FBEND" in buf and seen_end is None:
                seen_end = time.time()
        else:
            time.sleep(0.1)
        if seen_end and time.time() - seen_end > 1.5:
            break
    s.close()
    text = buf.decode("utf-8", errors="replace")
    rows = [ln for ln in text.splitlines() if ln.startswith("|") and ln.endswith("|")]
    if not rows:
        print("KEIN DUMP erhalten. Rohausgabe:")
        print(text[-800:])
        return
    print(f"{len(rows)} Zeilen a {len(rows[0]) - 2} Zeichen:")
    print("+" + "-" * (len(rows[0]) - 2) + "+")
    for r in rows:
        print(r)
    print("+" + "-" * (len(rows[0]) - 2) + "+")


main()
