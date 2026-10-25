import struct

with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    data = f.read()

# 0x572a0: ldr r3, [pc, #0x1fc] -> 0x572a0 + 4 + 0x1fc = 0x574a0!
val = struct.unpack('<I', data[0x574a0-0x10000:0x574a0-0x10000+4])[0]
print('0x574a0 string:', data[val-0x10000:val-0x10000+60].split(b'\x00')[0])
