import struct

with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    data = f.read()

cb2_ptr = struct.unpack('<I', data[0x5c9e0-0x10000:0x5c9e0-0x10000+4])[0]
print("ModelSelectWindow Callback address:", hex(cb2_ptr))
