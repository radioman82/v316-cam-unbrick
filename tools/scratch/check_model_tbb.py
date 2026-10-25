with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    data = f.read()

# tbb table is at 0x66ede - 0x10000 = 0x56ede
table = data[0x56ede:0x56ede+7]
base = 0x66ede
for idx, b in enumerate(table):
    target = base + b * 2
    keycode = 0x82 + idx
    print(f"Key {hex(keycode)} ({keycode}) -> offset {b} -> target {hex(target)}")
