"""Install the clipped-paint GUI startup fix and remove delayed key replay."""
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
    p.add_argument('binary', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--tools', required=True, type=Path)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    image = args.image.read_bytes()
    assert len(image) == 16777216
    app = args.binary.read_bytes()
    assert app[:5] == b'\x7fELF\x01'
    sq_source = args.output/'source.squashfs'
    sq_source.write_bytes(image[0x400000:0xe80000])
    old_tar, changed_tar, verify_tar = [args.output/n for n in ('source.tar','gui-startup.tar','verify.tar')]
    with old_tar.open('wb') as out:
        subprocess.run([str(args.tools/'sqfs2tar.exe'), '-r', '.', '-s', str(sq_source)], stdout=out, check=True)
    init = 'etc/init.d/S01app'
    binary = 'usr/bin/sdvcam'
    helper = 'opt/cam/startup_menu.sh'
    line = b'    sh /opt/cam/startup_menu.sh >/tmp/startup-menu.log 2>&1 </dev/null &\n'
    found = set()
    with tarfile.open(old_tar) as original, tarfile.open(changed_tar, 'w', format=tarfile.PAX_FORMAT) as changed:
        for member in original:
            m = copy.copy(member)
            path = m.name.removeprefix('./')
            if path == helper:
                found.add(path)
                continue
            data = original.extractfile(member).read() if m.isfile() else None
            if path == binary:
                data = app
                found.add(path)
            elif path == init:
                assert data.count(line) == 1
                data = data.replace(line, b'')
                found.add(path)
            if data is not None:m.size = len(data)
            changed.addfile(m, io.BytesIO(data) if data is not None else None)
    assert found == {init,binary,helper}
    sq = args.output/'gui-startup.squashfs'
    with changed_tar.open('rb') as src:
        subprocess.run([str(args.tools/'tar2sqfs.exe'), '-s', '-c', 'xz', '-b', '131072', '-q', str(sq)], stdin=src, check=True)
    assert sq.stat().st_size <= 0xa80000
    with verify_tar.open('wb') as out:
        subprocess.run([str(args.tools/'sqfs2tar.exe'), '-r', '.', '-s', str(sq)], stdout=out, check=True)
    before, after = tar_index(old_tar), tar_index(verify_tar)
    assert set(before)-set(after) == {helper}
    assert not set(after)-set(before)
    changed = {key for key in after if after[key] != before[key]}
    assert changed == {init,binary}, changed
    for path in changed:assert before[path][:8] == after[path][:8]
    target_data = image[:0x400000]+sq.read_bytes().ljust(0xa80000,b'\xff')+image[0xe80000:]
    target = args.output/'V316CM_GUI_STARTUP_PRIVATE_16MiB.bin'
    target.write_bytes(target_data)
    package = args.output/'firmware-update.bin'
    package.write_bytes(build(target_data))
    assert package.read_bytes()[512:] == target_data
    report = {'status':'offline verified; not yet installed','sha256':hashlib.sha256(target_data).hexdigest(),'source_sha256':hashlib.sha256(image).hexdigest(),'package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'app_md5':hashlib.md5(app).hexdigest(),'rootfs_md5':hashlib.md5(target_data[0x400000:0xe80000]).hexdigest(),'rootfs_bytes':sq.stat().st_size,'modified':sorted(changed),'removed':[helper],'entries_verified':len(after),'startup_audio_unchanged':True,'private':True}
    (args.output/'manifest.json').write_text(json.dumps(report,indent=2))
    (args.output/'SHA256SUMS.txt').write_text(''.join(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}\n' for f in (target,package)))
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    main()
