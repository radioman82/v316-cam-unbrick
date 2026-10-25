import hashlib, serial, time

with open('d:/v316cm/sdvcam_v5', 'rb') as f:
    expected_md5 = hashlib.md5(f.read()).hexdigest()
print("Expected MD5:", expected_md5)

s = serial.Serial('COM11', 115200, timeout=2)
def run(cmd):
    s.write(cmd.encode() + b'\n')
    time.sleep(0.2)
    out = b''
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.05)
    return out.decode('utf-8', errors='replace')

# 1. Kill sdvcam and unmount
run('killall -9 sdvcam 2>/dev/null')
time.sleep(1)
run('umount /usr/bin/sdvcam 2>/dev/null')
run('umount /usr/share/minigui/res/images 2>/dev/null')

# 2. Apply patches with dd
# Patch 1: 0x3ed64 = 257380 -> 0x01, 0xe0, 0x00, 0xbf
run('printf "\\x01\\xe0\\x00\\xbf" | dd of=/mnt/extsd/sdvcam bs=1 seek=257380 conv=notrunc')

# Patch 2: 0x472ba = 291514 -> 0x09, 0xe0
run('printf "\\x09\\xe0" | dd of=/mnt/extsd/sdvcam bs=1 seek=291514 conv=notrunc')

# Patch 3: 0x4b034 = 307252 -> 0x3e, 0xe0
run('printf "\\x3e\\xe0" | dd of=/mnt/extsd/sdvcam bs=1 seek=307252 conv=notrunc')

# Patch 4: 0x4b996 = 309654 -> 0x07, 0xe0
run('printf "\\x07\\xe0" | dd of=/mnt/extsd/sdvcam bs=1 seek=309654 conv=notrunc')

# Patch 5: 0x4b9b2 = 309682 -> 0x08, 0xe0
run('printf "\\x08\\xe0" | dd of=/mnt/extsd/sdvcam bs=1 seek=309682 conv=notrunc')

# Patch 6: 0x4b9d0 = 309712 -> 0x46, 0xd0, 0x00, 0xbf
run('printf "\\x46\\xd0\\x00\\xbf" | dd of=/mnt/extsd/sdvcam bs=1 seek=309712 conv=notrunc')

run('sync')

# 3. Check md5
actual = run('md5sum /mnt/extsd/sdvcam')
print("Camera MD5 output:", actual)

if expected_md5 in actual:
    print("SUCCESS: MD5 MATCHES 100%!")
else:
    print("ERROR: MD5 mismatch!")

s.close()
