with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    data = f.read()

off = 0x502a4 - 0x10000
import struct
for i in range(-0x40, 0x40, 4):
    p = off + i
    w = struct.unpack('<I', data[p:p+4])[0]
    print(hex(p + 0x10000), ":", hex(w))
