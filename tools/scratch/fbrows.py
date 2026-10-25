"""Framebuffer zeilenweise, verlustsicher lesen und als ASCII zeigen.

Jede Zeile wird einzeln gelesen und mit einer Laengenpruefung quittiert.
Bei Zeilenverlust wird die Zeile wiederholt. Ausgabe: 320 px -> 80 Zeichen
(jedes 4. Pixel), 480 Zeilen -> jede 4. Zeile (120 Zeilen).

usage: python fbrows.py [--step 4] [--rows 240]
"""
import argparse
import sys
import time

import serial

ap = argparse.ArgumentParser()
ap.add_argument("--step", type=int, default=4, help="jedes n-te Pixel")
ap.add_argument("--rows", type=int, default=240, help="nur die ersten n Zeilen")
ap.add_argument("--rowstep", type=int, default=4, help="jede n-te Bildzeile")
args = ap.parse_args()

W = 320
COLS = W // args.step

REMOTE = r"""
grab() {
  y=$1
  n=0
  while [ $n -lt 4 ]; do
    L=`dd if=/dev/fb0 bs=1280 skip=$y count=1 2>/dev/null | od -An -tu1 -v -w1280 | awk -v st=%(STEP)d '{s="";for(j=1;j<=1280;j+=4*st){v=$j;c=int(v/26);if(c>9)c=9;s=s substr(" .:-=+*#%%@",c+1,1)}printf "%%s", s}'`
    if [ ${#L} -eq %(COLS)d ]; then
      echo "R$y:${#L}:$L"
      return
    fi
    n=$((n+1))
  done
  echo "R$y:FAIL:"
}
i=0
while [ $i -lt %(ROWS)d ]; do
  grab $i
  i=$((i+%(ROWSTEP)d))
done
echo FBEND
"""


def main():
    s = serial.Serial("COM11", 115200, timeout=3)
    time.sleep(0.2)
    s.reset_input_buffer()
    script = REMOTE % {"ROWS": args.rows, "STEP": args.step, "ROWSTEP": args.rowstep, "COLS": COLS}
    s.write(("cat > /tmp/fbr.sh <<'XEOF'\n" + script + "XEOF\nsh /tmp/fbr.sh\n").encode())

    buf = b""
    t0 = time.time()
    while time.time() - t0 < 90:
        chunk = s.read(s.in_waiting or 1)
        if chunk:
            buf += chunk
            if b"FBEND" in buf:
                time.sleep(1.0)
                buf += s.read(s.in_waiting)
                break
    s.close()

    text = buf.decode("utf-8", errors="replace")
    rows = {}
    bad = 0
    for ln in text.splitlines():
        if not ln.startswith("R") or ":" not in ln:
            continue
        try:
            _, n, payload = ln.split(":", 2)
            n = int(n)
        except ValueError:
            continue
        if len(payload) != n:
            bad += 1
            continue
        rows[int(_[1:])] = payload

    if not rows:
        print("KEIN DUMP. Rohausgabe:")
        print(text[-1200:])
        return

    want = list(range(0, args.rows, args.rowstep))
    missing = [y for y in want if y not in rows]
    print(f"{len(rows)}/{len(want)} Zeilen gelesen, {bad} verworfen, "
          f"{len(missing)} fehlen: {missing[:20]}")
    print("+" + "-" * COLS + "+")
    for y in want:
        print("|" + rows.get(y, "?" * COLS) + "|")
    print("+" + "-" * COLS + "+")


main()
