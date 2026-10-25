import os

with open('d:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/etc/init.d/S01app', 'r') as f:
    orig = f.read()

lines = orig.splitlines()
insert_idx = 59
start_app_idx = 68

mount_code = [
    '    for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do',
    '        if grep -q \'/mnt/extsd\' /proc/mounts; then',
    '            break',
    '        fi',
    '        if [ -b /dev/mmcblk0 ]; then',
    '            mount -t vfat /dev/mmcblk0 /mnt/extsd 2>/dev/null && break',
    '            mount -t vfat /dev/mmcblk0p1 /mnt/extsd 2>/dev/null && break',
    '        fi',
    '        sleep 0.2',
    '    done',
    '',
    '    if [ -d "/mnt/extsd/custom_ui" ]; then',
    '        mount --bind /mnt/extsd/custom_ui /usr/share/minigui/res/images',
    '    fi',
    '    if [ -f "/mnt/extsd/sdvcam" ]; then',
    '        mount --bind /mnt/extsd/sdvcam /usr/bin/sdvcam',
    '    fi',
]

new_lines = lines[:insert_idx] + mount_code + lines[start_app_idx:]
with open('d:/v316cm/S01app_clean', 'w', newline='\n') as f:
    f.write('\n'.join(new_lines) + '\n')
print('Successfully generated d:/v316cm/S01app_clean')
