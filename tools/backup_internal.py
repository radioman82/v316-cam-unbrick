"""Snapshot all flash partitions, reconstruct locally using verified block deltas."""
import hashlib
import json
from pathlib import Path
import time
from camera_uart import CameraUART

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'firmware/V316CM_WORKING_FULL_IMAGE_16MB.bin'
SIZES = [0x100000,0x300000,0xa80000,0x80000,0x20000,0x60000,0x80000]

def main():
    stamp = time.strftime('%Y%m%d-%H%M%S')
    out = ROOT.parent / ('recovery-internal-' + stamp)
    out.mkdir()
    remote = '/mnt/extsd/.internal-backup-' + stamp
    c = CameraUART()
    try:
        c.run(f'mkdir -p {remote}')
        offset = 0
        full = bytearray()
        base = BASE.read_bytes()
        for part,size in enumerate(SIZES):
            target = f'{remote}/mtd{part}.bin'
            c.run(f'dd if=/dev/mtdblock{part} of={target} bs=65536 count={size//65536} 2>/dev/null && sync')
            expected = c.run(f'md5sum {target}').split()[0]
            hashes = c.run(f'i=0; while [ $i -lt {size//65536} ]; do dd if={target} bs=65536 skip=$i count=1 2>/dev/null | md5sum; i=$((i+1)); done',120).splitlines()
            assert len(hashes) == size//65536, (part,len(hashes))
            data = bytearray(base[offset:offset+size])
            changed = 0
            for i,line in enumerate(hashes):
                expected_chunk = line.split()[0]
                chunk = data[i*65536:(i+1)*65536]
                if hashlib.md5(chunk).hexdigest() != expected_chunk:
                    c.run(f'dd if={target} of={remote}/chunk bs=65536 skip={i} count=1 2>/dev/null')
                    chunk = c.read(f'{remote}/chunk')
                    assert len(chunk) == 65536 and hashlib.md5(chunk).hexdigest() == expected_chunk
                    data[i*65536:(i+1)*65536] = chunk
                    changed += 1
            assert hashlib.md5(data).hexdigest() == expected
            (out/f'mtd{part}.bin').write_bytes(data)
            full.extend(data)
            offset += size
            print('BACKUP',part,size,'changed blocks',changed,'MD5',expected,flush=True)
        assert len(full)==16777216
        (out/'current-16MiB.bin').write_bytes(full)
        (out/'manifest.json').write_text(json.dumps({'remote':remote,'sha256':hashlib.sha256(full).hexdigest()},indent=2))
        # Preserve settings without printing private values.
        for name,path in [('setting.lua','/tmp/data/setting.lua'),('wlan.conf','/mnt/extsd/wlan.conf')]:
            data=c.read(path)
            assert hashlib.md5(data).hexdigest()==c.run(f'md5sum {path}').split()[0]
            (out/name).write_bytes(data)
        print('BACKUP_COMPLETE',out,flush=True)
    finally:
        c.close()

if __name__=='__main__':
    main()
