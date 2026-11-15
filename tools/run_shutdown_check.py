"""Observe native power-key shutdown and save SD frames plus UART diagnostics."""
import argparse
import base64
import json
from pathlib import Path
import struct
import sys
import time

from camera_uart import CameraUART


def main():
    sys.stdout.reconfigure(errors='replace')
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('output',type=Path)
    args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    remote='/mnt/extsd/shutdown-check-20261102-2'
    c=CameraUART()
    try:
        status=json.loads(c.run('/opt/cam/bin/ct9000-control status'))
        assert not status['recording']
        c.run(f'test ! -e {remote} && mkdir {remote}')
        script=f'#!/bin/sh\ni=0\nwhile [ "$i" -lt 60 ]; do\n dd if=/dev/fb0 of={remote}/frame-$i.raw bs=307200 count=1 2>/dev/null || exit 1\n i=$((i+1))\n sleep 0.1\ndone\nsync\n'
        encoded=base64.b64encode(script.encode()).decode()
        c.run(f'printf %s {encoded} | /opt/cam/bin/busybox base64 -d > /tmp/codex-shutdown-capture.sh')
        for name,value in [('press',1),('release',0)]:
            data=struct.pack('<iiHHi',0,0,1,116,value)+struct.pack('<iiHHi',0,0,0,0,0)
            encoded=base64.b64encode(data).decode()
            c.run(f'printf %s {encoded} | /opt/cam/bin/busybox base64 -d > /tmp/codex-power-{name}')
        command=f'sh /tmp/codex-shutdown-capture.sh >{remote}/capture.log 2>&1 </dev/null & tail -n 0 -f /tmp/sdvcam.log & sleep 0.2; cat /tmp/codex-power-press > /dev/input/event1; sleep 3; cat /tmp/codex-power-release > /dev/input/event1\n'
        c.port.write(command.encode())
        end=time.monotonic()+25
        capture=bytearray()
        while time.monotonic()<end:
            data=c.port.read(c.port.in_waiting or 1)
            if data:
                capture.extend(data)
                print(data.decode('ascii',errors='replace'),end='',flush=True)
        (args.output/'shutdown-console.txt').write_bytes(capture)
        (args.output/'capture.json').write_text(json.dumps({'sd_capture_folder':remote,'before_shutdown':status,'power_key':'event1 KEY_POWER 116, held 3 seconds','display_observation':'await user observation'},indent=2))
    finally:
        c.port.close()


if __name__=='__main__':main()
