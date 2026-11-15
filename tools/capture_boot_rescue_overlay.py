"""Add the repaired, hash-checked overlay to the already verified boot image."""
import argparse
import hashlib
import json
from pathlib import Path

from camera_uart import CameraUART


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder', type=Path)
    args = p.parse_args()
    source = args.folder/'V316CM_BOOT_MENU_PRIVATE_16MiB.bin'
    image = source.read_bytes()
    c = CameraUART()
    try:
        c.run('test ! -e /overlay/upperdir/etc/init.d/S01app && cmp /etc/init.d/S01app /squashfs/etc/init.d/S01app')
        remote = '/tmp/codex-boot-menu-overlay.bin'
        c.run(f'dd if=/dev/mtdblock3 of={remote} bs=65536 count=8 2>/dev/null && test $(wc -c < {remote}) -eq 524288')
        expected = c.run(f'md5sum {remote}').split()[0]
        data = c.read(remote, 90)
        assert len(data) == 524288 and hashlib.md5(data).hexdigest() == expected
        (args.folder/'repaired-overlay-mtd3.bin').write_bytes(data)
        full = image[:0xe80000]+data+image[0xf00000:]
        assert len(full) == 16777216
        target = args.folder/'V316CM_BOOT_MENU_RESCUE_PRIVATE_16MiB.bin'
        assert not target.exists()
        target.write_bytes(full)
        assert target.read_bytes() == full
        report = {'status': 'verified rootfs image with camera-MD5-checked repaired overlay; no FEL restore test performed', 'source_image': source.name, 'sha256': hashlib.sha256(full).hexdigest(), 'overlay_md5': expected, 'old_S01app_overlay_absent': True, 'private': True}
        (args.folder/'rescue-overlay.json').write_text(json.dumps(report, indent=2))
        (args.folder/'SHA256SUMS-rescue.txt').write_text(f"{report['sha256']}  {target.name}\n")
        print(json.dumps(report, indent=2), flush=True)
    finally:
        c.close()


if __name__ == '__main__':
    main()
