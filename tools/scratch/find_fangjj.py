with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam', 'rb') as f:
    data = f.read()

import re
strs = re.findall(b'\[fangjj\][^\x00]*', data)
for s in strs:
    try:
        print(s.decode('latin1'))
    except:
        pass
