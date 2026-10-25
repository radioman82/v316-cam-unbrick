import hashlib, serial, time

EXPECTED_MD5 = "45a744f66b8f3534dfb77f8de559967a"

with open("d:/v316cm/sdvcam_4tiles_v2", "rb") as f:
    local_data = f.read()
    actual_local_md5 = hashlib.md5(local_data).hexdigest()

assert actual_local_md5 == EXPECTED_MD5, f"Local MD5 mismatch: {actual_local_md5}"
print("Local sdvcam_4tiles_v2 MD5 verified:", EXPECTED_MD5)

s = serial.Serial('COM11', 115200, timeout=2)
def run(cmd):
    s.write(cmd.encode() + b'\n')
    time.sleep(0.2)
    out = b''
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.05)
    return out.decode('utf-8', errors='replace')

print("\n1. Stopping running sdvcam and unmounting...")
run('killall -9 sdvcam 2>/dev/null')
time.sleep(1)
run('umount /usr/bin/sdvcam 2>/dev/null')

# Patches to apply to /mnt/extsd/sdvcam (which is currently exact v8)
patches = [
    (0x4afe0, "Action Dispatcher (76 bytes)", local_data[0x4afe0 : 0x4afe0 + 76]),
    (0x4ba46, "Front button re-opens menu (4 bytes)", bytes.fromhex("fff7f3ba")),
    (0x59852, "Front button in menu cycles tiles (1 byte)", bytes.fromhex("0b")),
    (0x5c0ee, "Boot hook in OnWindowLoaded (16 bytes)", bytes.fromhex("03b0bde83040eef79cbf00bf00bf00bf")),
    (0x1f32a2, "Streaming command string", b"/mnt/extsd/start_streaming.sh &\x00"),
]

print("\n2. Applying patches to /mnt/extsd/sdvcam...")
for off, name, patch_bytes in patches:
    hex_str = ''.join(f'\\x{b:02x}' for b in patch_bytes)
    cmd = f'printf "{hex_str}" | dd of=/mnt/extsd/sdvcam bs=1 seek={off} conv=notrunc'
    print(f"  Patching {name} @ {hex(off)} ({len(patch_bytes)} bytes)...")
    run(cmd)

run('sync')

print("\n3. Verifying MD5 of /mnt/extsd/sdvcam on camera...")
actual = run('md5sum /mnt/extsd/sdvcam')
print(actual)

if EXPECTED_MD5 in actual:
    print(">>> SUCCESS: /mnt/extsd/sdvcam MATCHES 4tiles_v2 100%! <<<")
else:
    print(">>> ERROR: MD5 mismatch on camera! <<<")
    s.close()
    exit(1)

print("\n4. Remounting /usr/bin/sdvcam and custom UI...")
run('mount --bind /mnt/extsd/sdvcam /usr/bin/sdvcam')
run('mount --bind /mnt/extsd/custom_ui /usr/share/minigui/res/images')

print("5. Starting app cleanly...")
run('/usr/bin/sdvcam &')
time.sleep(3)

print("Checking processes:")
print(run('ps | grep sdvcam'))

s.close()
print("All patches applied and camera app started!")
