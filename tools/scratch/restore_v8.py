import hashlib, serial, time

EXPECTED_MD5 = 'ee7425e348fc3d35d09ff62fc405860a'

with open('d:/v316cm/sdvcam_v8', 'rb') as f:
    v8_data = f.read()

s = serial.Serial('COM11', 115200, timeout=2)
def run(cmd):
    s.write(cmd.encode() + b'\n')
    time.sleep(0.2)
    out = b''
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.05)
    return out.decode('utf-8', errors='replace')

print("1. Stopping running sdvcam and unmounting...")
run('killall -9 sdvcam 2>/dev/null')
time.sleep(1)
run('umount /usr/bin/sdvcam 2>/dev/null')

# Restore chunks where 4tiles differed from v8
chunks = [
    (0x472ea, v8_data[0x472ea : 0x472ea + 4]),
    (0x4afe0, v8_data[0x4afe0 : 0x4afe0 + 76]),
    (0x4b9e6, v8_data[0x4b9e6 : 0x4b9e6 + 6]),
    (0x59852, v8_data[0x59852 : 0x59852 + 1]),
    (0x1f32a2, v8_data[0x1f32a2 : 0x1f32a2 + 38]),
]

print("2. Restoring v8 chunks on /mnt/extsd/sdvcam...")
for off, cbytes in chunks:
    hex_str = ''.join(f'\\x{b:02x}' for b in cbytes)
    cmd = f'printf "{hex_str}" | dd of=/mnt/extsd/sdvcam bs=1 seek={off} conv=notrunc'
    run(cmd)

run('sync')

print("3. Checking MD5 on camera...")
actual = run('md5sum /mnt/extsd/sdvcam')
print(actual)

if EXPECTED_MD5 in actual:
    print(">>> SUCCESS: Restored exact v8! <<<")
else:
    print(">>> MISMATCH! <<<")

print("4. Remounting and restarting sdvcam...")
run('mount --bind /mnt/extsd/sdvcam /usr/bin/sdvcam')
run('/usr/bin/sdvcam &')
time.sleep(2)
print("Processes:")
print(run('ps | grep sdvcam'))
s.close()
