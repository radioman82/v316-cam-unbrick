import hashlib, serial, time

EXPECTED_MD5 = 'c8c3ee1b53c5a17b40260bb7fc159741'

with open('d:/v316cm/sdvcam_v7', 'rb') as f:
    v7_data = f.read()
    actual_local_md5 = hashlib.md5(v7_data).hexdigest()

assert actual_local_md5 == EXPECTED_MD5, f"Local v7 MD5 mismatch: {actual_local_md5}"
print("Local sdvcam_v7 MD5 verified:", EXPECTED_MD5)

with open('d:/v316cm/sdvcam_v6', 'rb') as f:
    v6_data = f.read()

diffs = [i for i in range(len(v6_data)) if v6_data[i] != v7_data[i]]
from itertools import groupby
chunks = []
for k, g in groupby(enumerate(diffs), lambda ix: ix[0] - ix[1]):
    group = list(g)
    start = group[0][1]
    end = group[-1][1]
    length = end - start + 1
    chunks.append((start, v7_data[start:start+length]))

print(f"Total diff regions: {len(chunks)}, total changed bytes: {len(diffs)}")

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

print("2. Applying v7 patches to /mnt/extsd/sdvcam...")
for start, data in chunks:
    hex_str = ''.join(f'\\x{b:02x}' for b in data)
    cmd = f'printf "{hex_str}" | dd of=/mnt/extsd/sdvcam bs=1 seek={start} conv=notrunc'
    print(f"  Writing {len(data)} bytes at offset 0x{start:x}...")
    run(cmd)

run('sync')

print("\n3. Verifying MD5 of /mnt/extsd/sdvcam on camera...")
actual = run('md5sum /mnt/extsd/sdvcam')
print(actual)

if EXPECTED_MD5 in actual:
    print(">>> SUCCESS: /mnt/extsd/sdvcam MATCHES v7 100%! <<<")
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
