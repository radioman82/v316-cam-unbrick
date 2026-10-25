with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    orig = f.read()
with open('d:/v316cm/sdvcam_v5', 'rb') as f:
    v5 = f.read()

diffs = []
for i in range(len(orig)):
    if orig[i] != v5[i]:
        diffs.append((i, orig[i], v5[i]))

print('Total byte diffs:', len(diffs))
for i, o, n in diffs:
    print(f'offset {hex(i)}: {hex(o)} -> {hex(n)}')
