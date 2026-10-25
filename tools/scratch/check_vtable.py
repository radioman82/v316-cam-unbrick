import struct

with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    data = f.read()

vtable_ptr = struct.unpack('<I', data[0x69e70-0x10000:0x69e70-0x10000+4])[0]
print("vtable address:", hex(vtable_ptr))

# Now let us read the function pointers in this vtable:
# Specifically offset 0x6c!
fn_6c = struct.unpack('<I', data[vtable_ptr+0x6c-0x10000:vtable_ptr+0x6c-0x10000+4])[0]
print("Function at offset 0x6c:", hex(fn_6c))
