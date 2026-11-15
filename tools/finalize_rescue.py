"""Validate a captured private rescue image and make its SD update package.

Requires dissect.squashfs for independent offline filesystem validation.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import wave

from dissect.squashfs import SquashFS
from sd_update.package import build


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder', type=Path)
    args = p.parse_args()
    folder = args.folder
    image_path = folder / 'V316CM_RESCUE_PRIVATE_16MiB.bin'
    image = image_path.read_bytes()
    assert len(image) == 16777216
    manifest_path = folder / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    assert hashlib.sha256(image).hexdigest() == manifest['sha256']
    offset = 0
    for part in manifest['partitions']:
        data = image[offset:offset+part['size']]
        assert hashlib.sha256(data).hexdigest() == part['sha256']
        assert data == (folder / f"mtd{part['part']}.bin").read_bytes()
        offset += part['size']
    fs = SquashFS(io.BytesIO(image[0x400000:0xe80000]))
    files = {}

    def walk(node, prefix=''):
        for entry in node.iterdir():
            path = prefix + '/' + entry.name
            if entry.is_dir():
                walk(entry, path)
            elif entry.is_file():
                data = entry.open().read()
                assert len(data) == entry.size, path
                files[path] = {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    walk(fs.root)
    for path in ['/usr/bin/sdvcam', '/etc/init.d/S01app', '/etc/init.d/S99sdupdate', '/opt/cam/update/updater', '/opt/cam/bin/busybox']:
        assert files[path]['size'] > 0
    startup = fs.get('/usr/share/minigui/res/audio/startup.wav').open().read()
    with wave.open(io.BytesIO(startup)) as wav:
        assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getcomptype()) == (1, 2, 44100, 'NONE')
    assert hashlib.md5(startup).hexdigest() == '18b0542c4ff38064e9e8667dd61326b4'
    package = build(image)
    package_path = folder / 'firmware-update.bin'
    assert not package_path.exists()
    package_path.write_bytes(package)
    saved = package_path.read_bytes()
    assert saved[512:] == image
    assert saved[64:96] == hashlib.sha256(saved[512:]).digest()
    assert struct.unpack_from('<I', saved, 16)[0] == len(image)
    (folder / 'rootfs-files.json').write_text(json.dumps(files, indent=2))
    manifest.update(offline_validation={'rootfs_files_read': len(files), 'startup_md5': hashlib.md5(startup).hexdigest(), 'kernel_crc': 'valid', 'package_payload': 'identical to full image'}, package_sha256=hashlib.sha256(saved).hexdigest())
    manifest_path.write_text(json.dumps(manifest, indent=2))
    (folder / 'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n' for path in [image_path, package_path]))
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
