import struct

with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    data = f.read()

pos = data.find(b'poweroff -f')
print("string pos:", hex(pos))
str_vaddr = pos + 0x10000
ptr = struct.pack("<I", str_vaddr)
for i in range(0, len(data)-4, 4):
    if data[i:i+4] == ptr:
        print("pointer at:", hex(i + 0x10000))
