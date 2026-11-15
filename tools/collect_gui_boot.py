"""Collect the diagnostic framebuffer sequence and detect menu regressions."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.request

from PIL import Image
from camera_uart import CameraUART


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('host')
    p.add_argument('reference',type=Path)
    p.add_argument('output',type=Path)
    args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    reference=hashlib.sha256(Image.open(args.reference).convert('RGBA').tobytes()).hexdigest()
    c=CameraUART();pid=None
    try:
        c.run('test -f /mnt/extsd/gui-boot-sequence-20261102/complete')
        reply=c.run('/opt/cam/bin/busybox httpd -f -p 18080 -h /mnt/extsd/gui-boot-sequence-20261102 >/tmp/gui-boot-http.log 2>&1 </dev/null & echo $!')
        pid=next((line.split()[-1] for line in reversed(reply.splitlines()) if line.split() and line.split()[-1].isdigit()),None)
        assert pid.isdigit()
        classes=[]
        for i in range(40):
            with urllib.request.urlopen(f'http://{args.host}:18080/frame-{i}.raw',timeout=15) as response:raw=response.read()
            assert len(raw)==307200
            im=Image.frombytes('RGBA',(320,240),raw,'raw','BGRA')
            im.save(args.output/f'frame-{i:02}.png')
            classes.append('menu' if hashlib.sha256(im.tobytes()).hexdigest()==reference else 'other')
        first=classes.index('menu')
        assert all(label=='menu' for label in classes[first:]),classes
        report={'frames':40,'interval_seconds':0.2,'first_menu_frame':first,'no_regression_after_first_menu':True,'classes':classes,'reference':str(args.reference)}
        (args.output/'sequence.json').write_text(json.dumps(report,indent=2))
        print(json.dumps(report,indent=2),flush=True)
    finally:
        if pid and pid.isdigit():c.run(f'kill {pid} 2>/dev/null; true')
        c.close()


if __name__=='__main__':main()
