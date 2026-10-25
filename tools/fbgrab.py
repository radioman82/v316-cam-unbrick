"""Framebuffer der Kamera als ASCII-Kunst auslesen (serielle Konsole).

Liest /dev/fb0 (320x480, 32 bpp, stride 1280) zeilenweise, sampelt jedes
8. Pixel und gibt 30 Zeilen a 40 Zeichen aus. Uebertragen werden nur ~1,2 KB
statt 600 KB — das laeuft ueber 115200 Baud in wenigen Sekunden.

Damit laesst sich pruefen, ob wirklich das Menue auf dem Schirm steht.
Ein Log-Eintrag (z. B. function_select_window.cpp:129) beweist das NICHT,
denn diese Zeilen erscheinen bei jedem Boot.

Neben dem Bild wird auch geprueft, ob der Schirm statisch ist: drei
Framebuffer-Hashes im Abstand von 2 s. Gleiche Hashes = kein Livebild.

usage: python fbgrab.py [--port COM11]
"""
import argparse
import hashlib
import sys
import time

import serial

# BusyBox-sh: zeilenweise lesen, jedes 8. Byte (= jedes 8. Pixel, B-Kanal)
REMOTE_SCRIPT = r"""
y=0
while [ $y -lt 480 ]; do
  dd if=/dev/fb0 bs=1280 skip=$y count=1 2>/dev/null | od -An -tu1 -v -w1280 | awk '{s="";for(i=1;i<=1280;i+=32){v=$i;c=int(v/26);if(c>9)c=9;s=s substr(" .:-=+*#%@",c+1,1)}print "|" s "|"}'
  y=$((y+16))
done
echo FBEND
"""


def collect(ser, block, timeout=40.0):
    ser.reset_input_buffer()
    ser.write(block.encode())
    buf = b""
    t0 = time.time()
    seen_end = None
    while time.time() - t0 < timeout:
        if ser.in_waiting:
            buf += ser.read(ser.in_waiting)
            if b"FBEND" in buf and seen_end is None:
                seen_end = time.time()
        else:
            time.sleep(0.1)
        if seen_end and time.time() - seen_end > 1.5:
            break
    return buf.decode("utf-8", errors="replace")


def check_prompt(ser):
    """Passiv mitschauen, ob die Kamera im U-Boot haengt.

    Wichtig: In der U-Boot-Autoboot-Wartezeit bricht JEDES eintreffende Byte
    den Bootvorgang ab. Deshalb hier nur lesen, nie schreiben.
    """
    buf = b""
    t0 = time.time()
    while time.time() - t0 < 1.5:
        if ser.in_waiting:
            buf += ser.read(ser.in_waiting)
        else:
            time.sleep(0.05)
    text = buf.decode("utf-8", errors="replace")
    bad = ("sunxi#", "BOOT0", "U-Boot", "DRAM:")
    if any(k in text for k in bad):
        return False, text
    return True, text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="COM11")
    ap.add_argument("--baud", type=int, default=115200)
    a = ap.parse_args()

    ser = serial.Serial(a.port, a.baud, timeout=3)
    time.sleep(0.2)

    ok, pre = check_prompt(ser)
    if not ok:
        ser.close()
        print("ABBRUCH: Die Kamera haengt im Bootloader (U-Boot), nicht in der Shell.")
        print("Nichts senden! Im U-Boot-Prompt 'reset' eingeben und ~15 s warten.")
        print(f"Empfangen: {pre[-200:]!r}")
        return 2

    # 1) Statik-Test
    hashes = []
    for _ in range(3):
        ser.reset_input_buffer()
        ser.write(b"dd if=/dev/fb0 bs=1280 count=480 2>/dev/null | md5sum\n")
        time.sleep(2.0)
        out = ser.read(ser.in_waiting).decode("utf-8", errors="replace")
        for tok in out.split():
            if len(tok) == 32 and all(c in "0123456789abcdef" for c in tok):
                hashes.append(tok)
                break
    if len(hashes) == 3:
        static = len(set(hashes)) == 1
        print(f"Framebuffer-Hash: {hashes[0]}")
        print(f"Statik-Test: {'STATISCH (kein Livebild)' if static else 'DYNAMISCH (Livebild laeuft)'}")
        if not static:
            print(f"  Hashes: {hashes}")
    else:
        print(f"Statik-Test fehlgeschlagen (Hashes: {hashes})")

    # 2) ASCII-Abbild
    block = ("cat > /tmp/fb.sh <<'XEOF'\n" + REMOTE_SCRIPT +
             "XEOF\nsh /tmp/fb.sh\n")
    text = collect(ser, block)
    ser.close()

    rows = [ln for ln in text.splitlines() if ln.startswith("|") and ln.endswith("|")]
    if not rows:
        print("KEIN DUMP erhalten. Rohausgabe:")
        print(text[-800:])
        return 1

    w = len(rows[0]) - 2
    print(f"\n{len(rows)} Zeilen a {w} Zeichen:")
    print("+" + "-" * w + "+")
    for r in rows:
        print(r)
    print("+" + "-" * w + "+")
    return 0


if __name__ == "__main__":
    sys.exit(main())
