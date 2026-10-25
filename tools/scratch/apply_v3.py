"""
Deploy sdvcam_4tiles_v3 to the camera over COM11.

Restores the clean v8 from /mnt/extsd/sdvcam_v8_bak first, then writes only the
changed regions with dd (fast, no 3.4 MB upload).
"""
import hashlib, serial, time, sys

LOCAL = r"d:\v316cm\sdvcam_4tiles_v3"
EXPECTED_MD5 = "59ee359ada28b43f43a5f8564b2822b1"
V8_MD5 = "ee7425e348fc3d35d09ff62fc405860a"

with open(LOCAL, "rb") as f:
    local = f.read()
assert hashlib.md5(local).hexdigest() == EXPECTED_MD5, "local MD5 mismatch"
print("Local v3 verified:", EXPECTED_MD5)

CMD_STR = b"/mnt/extsd/start_streaming.sh &\x00"

# (offset, length) regions that differ from v8
REGIONS = [
    (0x4afe0, 76),              # C: action dispatcher
    (0x4ba46, 4),               # D: preview key -> open menu
    (0x59852, 1),               # B: menu key -> cycle tile
    (0x5c0ec, 18),              # A: boot hook + nop'ed guard
    (0x1f32a2, len(CMD_STR)),   # streaming command string (32 bytes)
]

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

print("\n[1] Stopping app and unmounting bind mounts...")
run("killall -9 sdvcam 2>/dev/null", 1.0)
run("umount /usr/bin/sdvcam 2>/dev/null")
run("umount /usr/share/minigui/res/images 2>/dev/null")

print("[2] Restoring clean v8 from /mnt/extsd/sdvcam_v8_bak")
print("    backup md5:", md5("/mnt/extsd/sdvcam_v8_bak"))
run("cp /mnt/extsd/sdvcam_v8_bak /mnt/extsd/sdvcam", 2.0)
run("sync", 1.0)
cur = md5("/mnt/extsd/sdvcam")
print("    restored md5:", cur)
if cur != V8_MD5:
    print(">>> restore failed - aborting <<<")
    s.close()
    sys.exit(1)

print("[3] Writing patched regions...")
for off, ln in REGIONS:
    chunk = local[off:off + ln]
    hexs = "".join("\\x%02x" % b for b in chunk)
    run(f'printf "{hexs}" | dd of=/mnt/extsd/sdvcam bs=1 seek={off} conv=notrunc 2>/dev/null', 0.5)
    print(f"    0x{off:06x}  {ln:2d} bytes")

run("sync", 1.2)

print("\n[4] Verifying MD5 on camera...")
out = md5("/mnt/extsd/sdvcam")
print("    " + out)
if out != EXPECTED_MD5:
    print(">>> MD5 MISMATCH - aborting, NOT remounting <<<")
    s.close()
    sys.exit(1)
print(">>> byte-exact match <<<")

print("\n[5] Remounting and starting app...")
run("mount --bind /mnt/extsd/sdvcam /usr/bin/sdvcam")
run("mount --bind /mnt/extsd/custom_ui /usr/share/minigui/res/images")
s.reset_input_buffer()
run("/usr/bin/sdvcam &", 1.0)

print("[6] Watching serial output for 8s...")
time.sleep(8)
buf = b""
while s.in_waiting:
    buf += s.read(s.in_waiting)
    time.sleep(0.1)
print("---- serial ----")
print(buf.decode("utf-8", errors="replace")[-3000:])
print("----------------")

print("[7] Process check:")
print(run("ps | grep sdvcam | grep -v grep", 0.8))
s.close()
