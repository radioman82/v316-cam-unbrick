"""Replace only startup.wav, preserving all other SquashFS file metadata/content."""
import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import wave

from dissect.squashfs import SquashFS
from sd_update.package import build

STARTUP = 'usr/share/minigui/res/audio/startup.wav'


def tar_index(path):
    result = {}
    with tarfile.open(path) as archive:
        for m in archive:
            key = m.name.removeprefix('./').rstrip('/')
            data = archive.extractfile(m).read() if m.isfile() else b''
            result[key] = (m.type, m.mode, m.uid, m.gid, m.mtime, m.linkname, m.devmajor, m.devminor, hashlib.sha256(data).hexdigest(), len(data))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('image', type=Path)
    p.add_argument('wav', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--tools', required=True, type=Path)
    args = p.parse_args()
    args.output.mkdir(exist_ok=False, parents=True)
    image = bytearray(args.image.read_bytes())
    assert len(image) == 16777216
    wav_data = args.wav.read_bytes()
    with wave.open(io.BytesIO(wav_data)) as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getcomptype()) == (1, 2, 44100, 'NONE')
        seconds = w.getnframes() / w.getframerate()
    source_sq = args.output / 'source.squashfs'
    source_sq.write_bytes(image[0x400000:0xe80000])
    source_tar = args.output / 'source.tar'
    changed_tar = args.output / 'startup-neu1.tar'
    with source_tar.open('wb') as out:
        subprocess.run([str(args.tools/'sqfs2tar.exe'), '--root-becomes', '.', '--no-skip', str(source_sq)], stdout=out, check=True)
    found = 0
    with tarfile.open(source_tar) as original, tarfile.open(changed_tar, 'w', format=tarfile.PAX_FORMAT) as changed:
        for member in original:
            m = copy.copy(member)
            if m.name.removeprefix('./') == STARTUP:
                assert m.isfile()
                m.size = len(wav_data)
                changed.addfile(m, io.BytesIO(wav_data))
                found += 1
            else:
                changed.addfile(m, original.extractfile(member) if m.isfile() else None)
    assert found == 1
    new_sq = args.output / 'startup-neu1.squashfs'
    with changed_tar.open('rb') as source:
        subprocess.run([str(args.tools/'tar2sqfs.exe'), '--no-skip', '--compressor', 'xz', '--block-size', '131072', '--quiet', str(new_sq)], stdin=source, check=True)
    assert new_sq.stat().st_size <= 0xa80000
    verify_tar = args.output / 'verify.tar'
    with verify_tar.open('wb') as out:
        subprocess.run([str(args.tools/'sqfs2tar.exe'), '--root-becomes', '.', '--no-skip', str(new_sq)], stdout=out, check=True)
    before, after = tar_index(source_tar), tar_index(verify_tar)
    assert before.keys() == after.keys()
    differences = [key for key in before if before[key] != after[key]]
    assert differences == [STARTUP], differences
    assert before[STARTUP][:8] == after[STARTUP][:8], 'startup metadata changed'
    fs = SquashFS(io.BytesIO(new_sq.read_bytes()))
    assert fs.get('/'+STARTUP).open().read() == wav_data
    assert fs.get('/usr/bin/sdvcam').open().read()[:4] == b'\x7fELF'
    original_bytes = bytes(image)
    image[0x400000:0xe80000] = new_sq.read_bytes().ljust(0xa80000, b'\xff')
    assert image[:0x400000] == original_bytes[:0x400000]
    assert image[0xe80000:] == original_bytes[0xe80000:]
    image_path = args.output / 'V316CM_STARTUP_NEU1_PRIVATE_16MiB.bin'
    image_path.write_bytes(image)
    package_path = args.output / 'firmware-update.bin'
    package_path.write_bytes(build(image))
    assert package_path.read_bytes()[512:] == image_path.read_bytes()
    report = {'status': 'offline verified; not yet installed', 'source_image_sha256': hashlib.sha256(original_bytes).hexdigest(), 'wav_source': str(args.wav.resolve()), 'wav_sha256': hashlib.sha256(wav_data).hexdigest(), 'wav_seconds': seconds, 'rootfs_bytes': new_sq.stat().st_size, 'rootfs_limit': 0xa80000, 'changed_files': differences, 'verified_tar_entries': len(before), 'sha256': hashlib.sha256(image).hexdigest(), 'package_sha256': hashlib.sha256(package_path.read_bytes()).hexdigest(), 'private': True}
    (args.output / 'manifest.json').write_text(json.dumps(report, indent=2))
    (args.output / 'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n' for path in [image_path, package_path]))
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
