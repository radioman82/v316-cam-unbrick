import re

with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    data = f.read()

strs = re.findall(b'[\x20-\x7e]{4,}', data)
for s in strs:
    dec = s.decode('ascii', errors='ignore')
    if any(k in dec.lower() for k in ['poweroff', 'shutdown', 'shut down']):
        print(dec)
