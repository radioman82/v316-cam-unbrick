"""
Deploy a locally built sdvcam variant to the camera over COM11.

usage: python apply_build.py <local_binary> <expected_md5>

Restores the clean v8 from /mnt/extsd/sdvcam_v8_bak first, then writes only the
changed regions with dd (fast, no 3.4 MB upload), verifies the MD5, remounts
and restarts the app.
"""
import hashlib, serial, time, sys

if len(sys.argv) < 3:
    sys.exit("usage: apply_build.py <local_binary> <expected_md5>")

LOCAL = sys.argv[1]
EXPECTED_MD5 = sys.argv[2].lower()
V8_MD5 = "ee7425e348fc3d35d09ff62fc405860a"
V8_LOCAL = r"d:\v316cm\sdvcam_v8"

with open(LOCAL, "rb") as f:
    local = f.read()
assert hashlib.md5(local).hexdigest() == EXPECTED_MD5, "local MD5 mismatch"
with open(V8_LOCAL, "rb") as f:
    v8 = f.read()

# derive changed regions automatically from the local v8
regions = []
i = 0
while i < len(v8):
    if v8[i] != local[i]:
        s = i
        while i < len(v8) and v8[i] != local[i]:
            i += 1
        regions.append((s, i - s))
    else:
        i += 1
print("changed regions vs v8:")
for off, ln in regions:
    print(f"  0x{off:06x}  {ln:3d} bytes")

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
run("killall -9 sdvcam 2>/dev/null", 1.0)
run("umount /usr/bin/sdvcam 2>/dev/null")
run("umount /usr/share/minigui/res/images 2>/dev/null")

print("[2] Restoring clean v8...")
if md5("/mnt/extsd/sdvcam_v8_bak") != V8_MD5:
    print("    backup missing/corrupt - recreating from current file")
    print(run("cp /mnt/extsd/sdvcam /mnt/extsd/sdvcam_v8_bak", 2.0))
run("cp /mnt/extsd/sdvcam_v8_bak /mnt/extsd/sdvcam", 2.0)
run("sync", 1.0)
cur = md5("/mnt/extsd/sdvcam")
print("    restored:", cur)
if cur != V8_MD5:
    sys.exit("restore failed - aborting")

print("[3] Writing patched regions...")
for off, ln in regions:
    chunk = local[off:off + ln]
    hexs = "".join("\\x%02x" % b for b in chunk)
    run(f'printf "{hexs}" | dd of=/mnt/extsd/sdvcam bs=1 seek={off} conv=notrunc 2>/dev/null', 0.5)
    print(f"    0x{off:06x}  {ln:3d} bytes")
run("sync", 1.2)

print("\n[4] Verifying MD5...")
got = md5("/mnt/extsd/sdvcam")
print("    " + got)
if got != EXPECTED_MD5:
    sys.exit(">>> MD5 MISMATCH - not remounting <<<")
print(">>> byte-exact match <<<")

print("\n[5] Remounting and starting app...")
run("mount --bind /mnt/extsd/sdvcam /usr/bin/sdvcam")
run("mount --bind /mnt/extsd/custom_ui /usr/share/minigui/res/images")
s.reset_input_buffer()
run("/usr/bin/sdvcam > /tmp/sdvcam.log 2>&1 &", 1.0)

print("[6] Waiting 12s for UI to settle...")
time.sleep(12)
buf = b""
while s.in_waiting:
    buf += s.read(s.in_waiting)
    time.sleep(0.1)
txt = buf.decode("utf-8", errors="replace")
print("---- serial tail ----")
print(txt[-1500:])
print("---------------------")
print("[7] Process:")
print(run("ps | grep sdvcam | grep -v grep", 0.8))
s.close()
