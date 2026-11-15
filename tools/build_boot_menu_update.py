"""Add a one-shot camera menu redraw after boot; retain all other files."""
import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

from build_startup_rescue import tar_index
from sd_update.package import build


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('image', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--tools', required=True, type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    image = args.image.read_bytes()
    assert len(image) == 16777216
    source = args.output / 'source.squashfs'
    source.write_bytes(image[0x400000:0xe80000])
    old_tar, new_tar, verify_tar = [args.output / n for n in ('source.tar', 'boot-menu.tar', 'verify.tar')]
    with old_tar.open('wb') as out:
        subprocess.run([str(args.tools/'sqfs2tar.exe'), '--root-becomes', '.', '--no-skip', str(source)], stdout=out, check=True)
    init_path = 'etc/init.d/S01app'
    helper_path = 'opt/cam/startup_menu.sh'
    helper = (Path(__file__).parent / 'ui_theme/startup_menu.sh').read_bytes().replace(b'\r\n', b'\n')
    found = 0
    with tarfile.open(old_tar) as original, tarfile.open(new_tar, 'w', format=tarfile.PAX_FORMAT) as changed:
        for member in original:
            m = copy.copy(member)
            assert m.name.removeprefix('./') != helper_path
            data = original.extractfile(member).read() if m.isfile() else None
            if m.name.removeprefix('./') == init_path:
                line = b'    /usr/bin/sdvcam >/tmp/sdvcam.log 2>&1 </dev/null &\n'
                assert data.count(line) == 1
                data = data.replace(line, line + b'    sh /opt/cam/startup_menu.sh >/tmp/startup-menu.log 2>&1 </dev/null &\n')
                m.size = len(data)
                found += 1
            changed.addfile(m, io.BytesIO(data) if data is not None else None)
        m = tarfile.TarInfo('./'+helper_path)
        m.mode, m.uid, m.gid, m.mtime, m.size = 0o755, 0, 0, 0, len(helper)
        changed.addfile(m, io.BytesIO(helper))
    assert found == 1
    sq = args.output / 'boot-menu.squashfs'
    with new_tar.open('rb') as src:
        subprocess.run([str(args.tools/'tar2sqfs.exe'), '--no-skip', '-c', 'xz', '-b', '131072', '-q', str(sq)], stdin=src, check=True)
    assert sq.stat().st_size <= 0xa80000
    with verify_tar.open('wb') as out:
        subprocess.run([str(args.tools/'sqfs2tar.exe'), '--root-becomes', '.', '--no-skip', str(sq)], stdout=out, check=True)
    before, after = tar_index(old_tar), tar_index(verify_tar)
    assert set(after)-set(before) == {helper_path}
    assert not set(before)-set(after)
    modified = [key for key in before if before[key] != after[key]]
    assert modified == [init_path], modified
    assert before[init_path][:8] == after[init_path][:8]
    assert before['usr/share/minigui/res/audio/startup.wav'] == after['usr/share/minigui/res/audio/startup.wav']
    new_image = image[:0x400000] + sq.read_bytes().ljust(0xa80000, b'\xff') + image[0xe80000:]
    target = args.output / 'V316CM_BOOT_MENU_PRIVATE_16MiB.bin'
    target.write_bytes(new_image)
    package = args.output / 'firmware-update.bin'
    package.write_bytes(build(new_image))
    assert package.read_bytes()[512:] == new_image
    report = {'status': 'offline verified; not installed', 'sha256': hashlib.sha256(new_image).hexdigest(), 'source_sha256': hashlib.sha256(image).hexdigest(), 'package_sha256': hashlib.sha256(package.read_bytes()).hexdigest(), 'rootfs_md5': hashlib.md5(new_image[0x400000:0xe80000]).hexdigest(), 'modified': modified, 'added': [helper_path], 'entries_verified': len(after), 'startup_audio_unchanged': True, 'rootfs_bytes': sq.stat().st_size, 'private': True}
    (args.output/'manifest.json').write_text(json.dumps(report, indent=2))
    (args.output/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}\n' for f in (target, package)))
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
