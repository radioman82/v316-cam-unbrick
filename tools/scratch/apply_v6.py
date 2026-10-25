import hashlib, serial, time

with open('d:/v316cm/sdvcam_v6', 'rb') as f:
    v6_data = f.read()
    expected_md5 = hashlib.md5(v6_data).hexdigest()
print("Expected MD5 (v6):", expected_md5)

patch_bytes = v6_data[0x4ba4e:0x4ba4e+26]

s = serial.Serial('COM11', 115200, timeout=2)
def run(cmd):
    s.write(cmd.encode() + b'\n')
    time.sleep(0.2)
    out = b''
    while s.in_waiting:
        out += s.read(s.in_waiting)
        time.sleep(0.05)
    return out.decode('utf-8', errors='replace')

# Kill and unmount
run('killall -9 sdvcam 2>/dev/null')
time.sleep(1)
run('umount /usr/bin/sdvcam 2>/dev/null')
run('umount /usr/share/minigui/res/images 2>/dev/null')

# Write 26 bytes at seek 0x4ba4e = 309838
cmd = 'printf "' + ''.join(f'\\x{b:02x}' for b in patch_bytes) + f'" | dd of=/mnt/extsd/sdvcam bs=1 seek=309838 conv=notrunc'
print(run(cmd))
run('sync')

actual = run('md5sum /mnt/extsd/sdvcam')
print("Camera MD5 output:", actual)

if expected_md5 in actual:
    print("SUCCESS: v6 MD5 MATCHES 100%!")
else:
    print("ERROR: MD5 mismatch!")

print("Restarting app via /etc/init.d/S01app start...")
run('/etc/init.d/S01app start')
time.sleep(4)
print("Processes:")
print(run('ps | grep sdvcam'))

s.close()
