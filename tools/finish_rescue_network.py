"""Finish an interrupted UART rescue capture using a temporary LAN HTTP server."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

from camera_uart import CameraUART
from rebuild_rescue_uart import SIZES


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder', type=Path)
    p.add_argument('url')
    args = p.parse_args()
    manifest_path = args.folder / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    assert len(manifest['partitions']) == 2
    c = CameraUART()
    try:
        for part in range(2, 7):
            remote = '/tmp/codex-rescue-snapshot/part'
            if part != 2:
                c.run(f'dd if=/dev/mtdblock{part} of={remote} bs=65536 count={SIZES[part]//65536} 2>/dev/null && test $(wc -c < {remote}) -eq {SIZES[part]}')
            expected = c.run(f'md5sum {remote}').split()[0]
            with urllib.request.urlopen(args.url + '/part', timeout=30) as response:
                data = response.read()
            assert len(data) == SIZES[part]
            assert hashlib.md5(data).hexdigest() == expected
            (args.folder / f'mtd{part}.bin').write_bytes(data)
            manifest['partitions'].append({'part': part, 'size': len(data), 'md5': expected, 'sha256': hashlib.sha256(data).hexdigest()})
            manifest_path.write_text(json.dumps(manifest, indent=2))
            print('PARTITION_VERIFIED', part, len(data), expected, flush=True)
        for iteration in range(2):
            for part in (0, 1, 2, 4, 5):
                expected = manifest['partitions'][part]['md5']
                actual = c.run(f'md5sum /dev/mtdblock{part}', 60).split()[0]
                assert actual == expected, (iteration, part, actual, expected)
        full = b''.join((args.folder / f'mtd{part}.bin').read_bytes() for part in range(7))
        assert len(full) == 16777216
        target = args.folder / 'V316CM_RESCUE_PRIVATE_16MiB.bin'
        assert not target.exists()
        target.write_bytes(full)
        assert target.read_bytes() == full
        manifest.update(status='partition snapshots verified by camera MD5; read-only regions confirmed twice; not FEL-readback tested', sha256=hashlib.sha256(full).hexdigest(), md5=hashlib.md5(full).hexdigest(), transport='UART reference deltas and temporary LAN HTTP')
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print('COMPLETE', target, flush=True)
    finally:
        c.close()


if __name__ == '__main__':
    main()
