#!/usr/bin/env python3
"""Deploy sdvcam_menu15 patches directly to /mnt/extsd/.sdvcam_patched.
"""
import serial, time, sys, os

PORT = "COM11"
EXPECTED_MD5 = "fd1711c58a006457e562b7f2b10e79f5"

s = serial.Serial(PORT, 115200, timeout=3)

def run(cmd, w=1.0):
    s.reset_input_buffer()
    s.write(cmd.encode() + b"\n")
    time.sleep(w)
    out = b""
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.05)
    return out.decode("utf-8", errors="replace")

print("1. Stopping sdvcam...")
print(run("killall -9 sdvcam", 1.0))

# Also restore from v11 base to be 100% clean
print("2. Ensuring clean v11 base...")
run("cat /mnt/extsd/sdvcam_bak_0ff4ffd9 > /mnt/extsd/.sdvcam_patched; sync", 1.5)
base_check = run("md5sum /mnt/extsd/.sdvcam_patched").strip()
print("Base on camera:", base_check)
assert "0ff4ffd99cb8377d9fe28cecc34d5dde" in base_check

# Patch 1: Dispatcher @ 0x4afe0 (80 bytes)
disp_bytes = bytes.fromhex(
    "30b504461546d4f814010ef0dffb032d09d0022d0ed00422002d00d000222046fff7a8fd30bd01234a2221462046fff7fbfc30bd43f2a220c0f22000c1f796ec30bd"
).ljust(80, b"\x00")
disp_oct = "".join("\\%03o" % b for b in disp_bytes)
cmd1 = f"printf '{disp_oct}' | dd of=/mnt/extsd/.sdvcam_patched bs=1 seek={0x4afe0} conv=notrunc 2>&1"
print("3. Applying Patch 1 (Dispatcher @ 0x4afe0)...")
print(run(cmd1, 1.0).strip())

# Patch 2: Shutter jump @ 0x4be08 (4 bytes)
shutter_bytes = bytes.fromhex("2fe000bf")
shutter_oct = "".join("\\%03o" % b for b in shutter_bytes)
cmd2 = f"printf '{shutter_oct}' | dd of=/mnt/extsd/.sdvcam_patched bs=1 seek={0x4be08} conv=notrunc 2>&1"
print("4. Applying Patch 2 (Foto shutter jump @ 0x4be08)...")
print(run(cmd2, 1.0).strip())

run("sync", 1.0)

print("5. Verifying MD5 on device...")
res = run("md5sum /usr/bin/sdvcam").strip()
print("Device MD5:", res)
if EXPECTED_MD5 not in res:
    print(f"ERROR: MD5 mismatch! Expected {EXPECTED_MD5}")
    s.close()
    sys.exit(1)

print("6. Saving copy as /mnt/extsd/sdvcam_menu15.bin...")
run("cp /mnt/extsd/.sdvcam_patched /mnt/extsd/sdvcam_menu15.bin; sync", 1.0)

print("7. Starting sdvcam...")
run("/etc/init.d/S01app start &", 2.0)

time.sleep(3)
ps_res = run("ps | grep sdvcam").strip()
print("Process:\n", ps_res)

s.close()
print("DEPLOY SUCCESSFUL!")
