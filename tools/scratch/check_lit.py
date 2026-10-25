import struct

with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    data = f.read()

v1 = struct.unpack('<I', data[0x69f3c-0x10000:0x69f3c-0x10000+4])[0]
v2 = struct.unpack('<I', data[0x69f40-0x10000:0x69f40-0x10000+4])[0]
print("v1:", hex(v1), "v2:", hex(v2))
if v1 > 0x10000 and v1 < 0x270000:
    print("v1 str:", data[v1-0x10000:v1-0x10000+40].split(b'\x00')[0])
if v2 > 0x10000 and v2 < 0x270000:
    print("v2 str:", data[v2-0x10000:v2-0x10000+40].split(b'\x00')[0])
