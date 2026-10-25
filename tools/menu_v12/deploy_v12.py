"""
Deploy sdvcam_menu_v12 to the camera over COM11.

v12 = v11 + 3 in-place patches that route the front button (keyCode 132,
short press) into the shutter handler (0x5ba4a) that the top OK button
(keyCode 130) uses.

Only the changed bytes are written with dd - no full 3.4 MB upload.
"""
import hashlib, serial, time, sys

LOCAL = r"d:\v316cm\sdvcam_menu_v12"
EXPECTED_MD5 = "0cda61d46070f20fa367310a5384d4ec"
V11_MD5 = "0ff4ffd99cb8377d9fe28cecc34d5dde"
V11_LOCAL = r"d:\v316cm\sdvcam_menu_v11"
REMOTE = "/mnt/extsd/sdvcam"

with open(LOCAL, "rb") as f:
    local = f.read()
assert hashlib.md5(local).hexdigest() == EXPECTED_MD5, "local MD5 mismatch"
with open(V11_LOCAL, "rb") as f:
    v11 = f.read()

regions = []
i = 0
while i < len(v11):
    if v11[i] != local[i]:
        s = i
        while i < len(v11) and v11[i] != local[i]:
            i += 1
        regions.append((s, i - s))
    else:
        i += 1
print("changed regions vs v11:")
for off, ln in regions:
    print(f"  0x{off:06x}  {ln:3d} bytes  {local[off:off+ln].hex()}")

s = serial.Serial("COM11", 115200, timeout=2)

def run(cmd, wait=0.35):
    s.reset_input_buffer()
    s.write(cmd.encode() + b"\n")
    time.sleep(wait)
    out = b""
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.05)
    return out.decode("utf-8", errors="replace")

def md5(path):
    o = run(f"md5sum {path}", 1.0)
    for tok in o.split():
        if len(tok) == 32 and all(c in "0123456789abcdef" for c in tok):
            return tok
    return "?"

print("\n[1] Stopping app, unmounting bind mounts...")
run("killall -9 sdvcam 2>/dev/null", 1.5)
run("umount /usr/bin/sdvcam 2>/dev/null")
run("umount /usr/share/minigui/res/images 2>/dev/null")

cur = md5(REMOTE)
print("    current on card:", cur)
if cur != V11_MD5:
    sys.exit(f"expected v11 {V11_MD5} on card, got {cur} - aborting")

print("[2] Writing patched bytes...")
for off, ln in regions:
    chunk = local[off:off + ln]
    hexs = "".join("\\x%02x" % b for b in chunk)
    run(f'printf "{hexs}" | dd of={REMOTE} bs=1 seek={off} conv=notrunc 2>/dev/null', 0.5)
    print(f"    0x{off:06x}  {ln:3d} bytes")
run("sync", 1.5)

print("\n[3] Verifying MD5...")
got = md5(REMOTE)
print("    " + got)
if got != EXPECTED_MD5:
    sys.exit(">>> MD5 MISMATCH - not remounting <<<")
print(">>> byte-exact match <<<")

print("\n[4] Remounting and starting app...")
run("mount --bind /mnt/extsd/sdvcam /usr/bin/sdvcam")
run("mount --bind /mnt/extsd/custom_ui /usr/share/minigui/res/images 2>/dev/null")
s.reset_input_buffer()
run("rm -f /tmp/A; /usr/bin/sdvcam > /tmp/sdvcam.log 2>&1 &", 1.0)

print("[5] Waiting 12s for UI to settle...")
time.sleep(12)
buf = b""
while s.in_waiting:
    buf += s.read(s.in_waiting)
    time.sleep(0.1)
print("---- serial tail ----")
print(buf.decode("utf-8", errors="replace")[-1200:])
print("---------------------")
print("[6] Process:")
print(run("ps | grep sdvcam | grep -v grep", 0.8))
print("[7] Deployed MD5:")
print("    " + md5("/usr/bin/sdvcam"))
s.close()
print("\nDONE - v12 active")
