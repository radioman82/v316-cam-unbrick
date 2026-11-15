"""Create a private, hash-checked flash snapshot without writing camera flash."""
import argparse
import hashlib
import json
from pathlib import Path
import time

from camera_uart import CameraUART

SIZES = [0x100000, 0x300000, 0xa80000, 0x80000, 0x20000, 0x60000, 0x80000]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('output', type=Path)
    p.add_argument('--baud', type=int, default=115200)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    reference = (Path(__file__).resolve().parents[1] / 'firmware/V316CM_WORKING_FULL_IMAGE_16MB.bin').read_bytes()
    c = CameraUART()
    original_baud = c.port.baudrate
    manifest = {'status': 'in progress', 'partitions': [], 'private': True}
    full = bytearray()
    remote = '/tmp/codex-rescue-snapshot'
    try:
        if args.baud != original_baud:
            c.port.write(f'stty {args.baud}\n'.encode())
            c.port.flush()
            time.sleep(.3)
            c.port.baudrate = args.baud
            print(c.run('echo BAUD_OK', 5), flush=True)
        c.run(f'test ! -e {remote} && mkdir {remote}')
        offset = 0
        for part, size in enumerate(SIZES):
            path = f'{remote}/part'
            c.run(f'dd if=/dev/mtdblock{part} of={path} bs=65536 count={size//65536} 2>/dev/null && test $(wc -c < {path}) -eq {size}')
            expected = c.run(f'md5sum {path}').split()[0]
            hashes = c.run(f'i=0; while [ $i -lt {size//65536} ]; do dd if={path} bs=65536 skip=$i count=1 2>/dev/null | md5sum; i=$((i+1)); done', 120).splitlines()
            assert len(hashes) == size // 65536
            data = bytearray(reference[offset:offset+size])
            for i, line in enumerate(hashes):
                digest = line.split()[0]
                chunk = data[i*65536:(i+1)*65536]
                if hashlib.md5(chunk).hexdigest() != digest:
                    c.run(f'dd if={path} of={remote}/chunk bs=65536 skip={i} count=1 2>/dev/null')
                    chunk = c.read(f'{remote}/chunk', 90)
                    assert len(chunk) == 65536 and hashlib.md5(chunk).hexdigest() == digest
                    data[i*65536:(i+1)*65536] = chunk
                print(f'PART {part} BLOCK {i+1}/{len(hashes)}', flush=True)
            assert hashlib.md5(data).hexdigest() == expected
            (args.output / f'mtd{part}.bin').write_bytes(data)
            manifest['partitions'].append({'part': part, 'size': size, 'md5': expected, 'sha256': hashlib.sha256(data).hexdigest()})
            full.extend(data)
            offset += size
            (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        assert len(full) == 16777216
        target = args.output / 'V316CM_RESCUE_PRIVATE_16MiB.bin'
        target.write_bytes(full)
        assert target.read_bytes() == full
        manifest.update(status='UART snapshot verified blockwise and partitionwise; not FEL-readback tested', sha256=hashlib.sha256(full).hexdigest(), md5=hashlib.md5(full).hexdigest())
        (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        print('COMPLETE', target, manifest['sha256'], flush=True)
    finally:
        if c.port.is_open:
            if c.port.baudrate != original_baud:
                c.port.write(f'stty {original_baud}\n'.encode())
                c.port.flush()
                time.sleep(.3)
                c.port.baudrate = original_baud
            c.close()


if __name__ == '__main__':
    main()
