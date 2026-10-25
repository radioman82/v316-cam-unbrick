with open(r'd:\v316cm\Firmware\firm\versuch6\_full_img_verbose.fex.extracted\squashfs-root\usr\share\minigui\res\lang\zh-DE.xml', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

print('Length of zh-DE.xml:', len(text), 'chars')
import re
items = re.findall(r'<string name="([^"]+)">([^<]+)</string>', text)
print('Total string entries:', len(items))
for k, v in items[:30]:
    print(f'{k:30} : {v}')
