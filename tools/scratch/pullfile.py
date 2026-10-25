"""Datei ueber die serielle Konsole holen (chunkweise hex, mit Pruefsumme).

usage: python pullfile.py /mnt/extsd/custom_ui/function_media.png local.png
"""
import hashlib
import os
import sys
import time

import serial

REMOTE = r"""
f="%(PATH)s"
sz=`wc -c < $f`
echo "SZ:$sz"
k=0
while [ $((k*64)) -lt $sz ]; do
  H=`dd if=$f bs=64 skip=$k count=1 2>/dev/null | od -An -tx1 -v | tr -d ' \n'`
  echo "C$k:${#H}:$H"
  sleep 0.05
  k=$((k+1))
done
md5sum $f
echo PULLEND
"""


def main():
    path, out = sys.argv[1], sys.argv[2]
    s = serial.Serial("COM11", 115200, timeout=3)
    time.sleep(0.2)
    s.reset_input_buffer()
    s.write(("cat > /tmp/pf.sh <<'XEOF'\n" + REMOTE % {"PATH": path} + "XEOF\nsh /tmp/pf.sh\n").encode())

    buf = b""
    t0 = time.time()
    while time.time() - t0 < 120:
        c = s.read(s.in_waiting or 1)
        if c:
            buf += c
            if b"PULLEND" in buf:
                time.sleep(0.8)
                buf += s.read(s.in_waiting)
                break
    s.close()

    text = buf.decode("utf-8", errors="replace")
    with open(out + ".raw.txt", "w", encoding="utf-8") as fh:
        fh.write(text)
    size = None
    chunks = {}
    remote_md5 = None
    for ln in text.splitlines():
        if ln.startswith("SZ:"):
            v = ln[3:].strip()
            if v.isdigit():
                size = int(v)
        elif ln.startswith("C") and ":" in ln:
            try:
                _, n, hx = ln.split(":", 2)
                n = int(n)
            except ValueError:
                continue
            if len(hx) != n or n % 2:
                continue
            chunks[int(_[1:])] = hx
        elif len(ln) >= 32 and ln[:32].replace(" ", "").isalnum() and path in ln:
            remote_md5 = ln[:32]

    if size is None:
        print("keine Groesse. Roh:")
        print(text[-600:])
        return

    need = (size + 63) // 64
    missing = [k for k in range(need) if k not in chunks]
    print(f"{path}: {size} B, {len(chunks)}/{need} Chunks, fehlen {len(missing)}")
    if missing:
        print("  fehlend:", missing[:20])

    data = bytearray()
    for k in range(need):
        if k in chunks:
            data += bytes.fromhex(chunks[k])
        else:
            data += b"\x00" * 64
    data = bytes(data[:size])

    got = hashlib.md5(data).hexdigest()
    print(f"  md5 lokal : {got}")
    print(f"  md5 remote: {remote_md5}")
    print("  OK" if got == remote_md5 else "  ABWEICHUNG")
    with open(out, "wb") as f:
        f.write(data)


main()
