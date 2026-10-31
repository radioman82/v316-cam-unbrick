"""Capture active SD runtime files, reusing byte-identical local assets."""
import hashlib
import argparse
from pathlib import Path
import tarfile
from camera_uart import CameraUART

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'internal-image-build/runtime'
ARCHIVE=ROOT.parent/'recovery-2026-10-29/sd-runtime-current-20261029.tar.gz'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',choices=['internal','sd'],default='internal')
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    candidates={}
    for folder in [ROOT/'firmware/ui_theme',ROOT/'firmware/splash',ROOT/'tools/streaming']:
        for p in folder.rglob('*'):
            if p.is_file():
                b=p.read_bytes()
                candidates[hashlib.md5(b).hexdigest()]=b
    if ARCHIVE.exists():
        with tarfile.open(ARCHIVE) as t:
            for member in t:
                if member.isfile():
                    b=t.extractfile(member).read()
                    candidates[hashlib.md5(b).hexdigest()]=b
    c=CameraUART()
    try:
        if args.source=='internal':
            roots={'/usr/share/minigui/res/images':'custom_ui','/usr/share/minigui/res/layout':'ui_theme/current/layout','/opt/cam/bin':'bin','/opt/cam/lib':'lib','/opt/cam/www':'www'}
            singles={'/usr/bin/sdvcam':'.sdvcam_patched','/usr/share/minigui/res/lang/zh-DE.xml':'ui_theme/current/zh-DE.xml','/data/wlan.conf':'wlan.conf'}
            singles.update({'/opt/cam/'+n:n for n in ['start_streaming.sh','stop_streaming.sh','network_mode.sh']})
        else:
            roots={'/mnt/extsd/'+n:n for n in ['custom_ui','ui_theme/current','bin','lib','www']}
            singles={'/mnt/extsd/'+n:n for n in ['.sdvcam_patched','start_streaming.sh','stop_streaming.sh','network_mode.sh','wlan.conf']}
        result=c.run(c.busybox+' find '+' '.join(roots)+' -type f -exec md5sum {} \\;',120)
        result+='\n'+c.run('md5sum '+' '.join(singles))
        (OUT.parent/'runtime-md5.txt').write_text(result)
        reused=downloaded=0
        for line in result.splitlines():
            h,path=line.split(None,1)
            assert len(h)==32
            relative=singles.get(path)
            if relative is None:
                prefix=next(p for p in roots if path.startswith(p+'/'))
                relative=roots[prefix]+path[len(prefix):]
            dest=OUT/relative
            data=candidates.get(h)
            if data is None:
                data=c.read(path,120)
                downloaded+=1
            else:
                reused+=1
            assert hashlib.md5(data).hexdigest()==h,path
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(data)
        print('RUNTIME_CAPTURED reused',reused,'downloaded',downloaded,flush=True)
        # Two independent reads: read-only regions must remain stable.
        for iteration in range(2):
            print('FLASH_READ',iteration,c.run('md5sum /dev/mtdblock0 /dev/mtdblock1 /dev/mtdblock2',120),flush=True)
    finally:
        c.close()

if __name__=='__main__':main()
