import hashlib, serial, time

EXPECTED_MD5 = 'ee7425e348fc3d35d09ff62fc405860a'

with open('d:/v316cm/sdvcam_v8', 'rb') as f:
    v8_data = f.read()
    actual_local_md5 = hashlib.md5(v8_data).hexdigest()

assert actual_local_md5 == EXPECTED_MD5, f"Local v8 MD5 mismatch: {actual_local_md5}"
print("Local sdvcam_v8 MD5 verified:", EXPECTED_MD5)

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
run('umount /usr/share/minigui/res/images 2>/dev/null')

print("2. Applying v8 patches (killing USB connect list on boot)...")
# 0x3f35a: 58 e0 00 bf
cmd1 = 'printf "\\x58\\xe0\\x00\\xbf" | dd of=/mnt/extsd/sdvcam bs=1 seek=258906 conv=notrunc'
print("  Writing at seek 0x3f35a (258906)...")
run(cmd1)

# 0x51a44: 00 20 70 47
cmd2 = 'printf "\\x00\\x20\\x70\\x47" | dd of=/mnt/extsd/sdvcam bs=1 seek=334404 conv=notrunc'
print("  Writing at seek 0x51a44 (334404)...")
run(cmd2)

run('sync')

print("\n3. Verifying MD5 of /mnt/extsd/sdvcam on camera...")
actual = run('md5sum /mnt/extsd/sdvcam')
print(actual)

if EXPECTED_MD5 in actual:
    print(">>> SUCCESS: /mnt/extsd/sdvcam MATCHES v8 100%! <<<")
else:
    print(">>> ERROR: MD5 mismatch on camera! <<<")
    s.close()
    exit(1)

print("\n4. Restarting app via /etc/init.d/S01app start...")
run('/etc/init.d/S01app start')
time.sleep(3)

print("Checking processes:")
print(run('ps | grep sdvcam'))

s.close()
print("Done!")
