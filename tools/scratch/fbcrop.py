"""Einen Bildschirmausschnitt zeilenweise, verlustsicher lesen.

usage: python fbcrop.py --x0 0 --x1 160 --y0 70 --y1 104 [--step 1]
"""
import argparse
import time

import serial

ap = argparse.ArgumentParser()
ap.add_argument("--x0", type=int, default=0)
ap.add_argument("--x1", type=int, default=320)
ap.add_argument("--y0", type=int, default=0)
ap.add_argument("--y1", type=int, default=480)
ap.add_argument("--step", type=int, default=1)
ap.add_argument("--rowstep", type=int, default=2)
args = ap.parse_args()

COLS = (args.x1 - args.x0) // args.step

REMOTE = r"""
grab() {
  y=$1
  n=0
  while [ $n -lt 5 ]; do
    L=`dd if=/dev/fb0 bs=1280 skip=$y count=1 2>/dev/null | od -An -tu1 -v -w1280 | awk -v a=%(X0)d -v b=%(X1)d -v st=%(STEP)d '{s="";for(j=4*a+1;j<=4*b;j+=4*st){v=$j;c=int(v/26);if(c>9)c=9;s=s substr(" .:-=+*#%%@",c+1,1)}printf "%%s", s}'`
    if [ ${#L} -eq %(COLS)d ]; then
      echo "R$y:${#L}:$L"
      return
    fi
    n=$((n+1))
  done
  echo "R$y:FAIL:"
}
y=%(Y0)d
while [ $y -lt %(Y1)d ]; do
  grab $y
  y=$((y+%(ROWSTEP)d))
done
echo CROPEND
"""


def main():
    s = serial.Serial("COM11", 115200, timeout=3)
    time.sleep(0.2)
    s.reset_input_buffer()
    script = REMOTE % {"X0": args.x0, "X1": args.x1, "STEP": args.step,
                       "Y0": args.y0, "Y1": args.y1,
                       "ROWSTEP": args.rowstep, "COLS": COLS}
    s.write(("cat > /tmp/fbc.sh <<'XEOF'\n" + script + "XEOF\nsh /tmp/fbc.sh\n").encode())

    buf = b""
    t0 = time.time()
    while time.time() - t0 < 90:
        c = s.read(s.in_waiting or 1)
        if c:
            buf += c
            if b"CROPEND" in buf:
                time.sleep(0.6)
                buf += s.read(s.in_waiting)
                break
    s.close()

    text = buf.decode("utf-8", errors="replace")
    rows = {}
    for ln in text.splitlines():
        if not ln.startswith("R") or ":" not in ln:
            continue
        try:
            tag, n, payload = ln.split(":", 2)
            n = int(n)
        except ValueError:
            continue
        if len(payload) != n:
            continue
        rows[int(tag[1:])] = payload

    want = list(range(args.y0, args.y1, args.rowstep))
    miss = [y for y in want if y not in rows]
    print(f"x {args.x0}..{args.x1}  y {args.y0}..{args.y1}  "
          f"{len(rows)}/{len(want)} Zeilen, fehlen {len(miss)} {miss[:10]}")
    print("+" + "-" * COLS + "+")
    for y in want:
        print("|" + rows.get(y, "?" * COLS) + "|")
    print("+" + "-" * COLS + "+")


main()
