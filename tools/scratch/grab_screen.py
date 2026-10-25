"""Pull /dev/fb0 from the camera over COM11 and save it as a PNG."""
import serial, time, base64, gzip, sys, io

PORT, BAUD = "COM11", 115200
W, H = 320, 480

s = serial.Serial(PORT, BAUD, timeout=3)

def run(cmd, wait=1.5):
    s.reset_input_buffer()
    s.write(cmd.encode() + b"\n")
    time.sleep(wait)
    o = b""
    while s.in_waiting:
        o += s.read(s.in_waiting)
        time.sleep(0.1)
    return o.decode("utf-8", errors="replace")

def pull(fb="/dev/fb0", size=W * H * 4):
    run(f"dd if={fb} of=/tmp/fb.raw bs={size} count=1 2>/dev/null", 3.0)
    run("gzip -9 -c /tmp/fb.raw > /tmp/fb.gz", 3.5)
    s.reset_input_buffer()
    s.write(b"uuencode -m /tmp/fb.gz fb.gz\n")
    buf = b""
    t0 = time.time()
    while time.time() - t0 < 60:
        if s.in_waiting:
            buf += s.read(s.in_waiting)
            if b"\nend\n" in buf or buf.rstrip().endswith(b"end"):
                break
        else:
            time.sleep(0.05)
    return buf.decode("ascii", errors="replace")

raw_txt = pull()
lines = raw_txt.splitlines()
# keep only base64 payload lines
payload = []
started = False
for ln in lines:
    if ln.startswith("begin-base64"):
        started = True
        continue
    if ln.strip() == "====" or ln.strip() == "end":
        break
    if started:
        payload.append(ln.strip())
b64 = "".join(payload)
print("base64 chars:", len(b64))
data = base64.b64decode(b64 + "=" * (-len(b64) % 4))
print("gz bytes:", len(data))
raw = gzip.decompress(data)
print("raw bytes:", len(raw))

# 32bpp BGRA -> RGB
px = bytearray()
for i in range(0, min(len(raw), W * H * 4), 4):
    b, g, r = raw[i], raw[i + 1], raw[i + 2]
    px += bytes((r, g, b))

from PIL import Image
img = Image.frombytes("RGB", (W, H), bytes(px))
out = r"d:\v316cm\fb0_screen.png"
img.save(out)
print("saved", out, img.size)

# quick stats
colors = img.getcolors(maxcolors=100000)
colors.sort(reverse=True)
print("distinct colors:", len(colors), "top:", colors[:5])
