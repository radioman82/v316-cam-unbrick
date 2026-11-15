"""Watch the UART; start an SD framebuffer sequence at the first boot shell."""
import argparse
import base64
from pathlib import Path
import time
import sys

import serial


def main():
    sys.stdout.reconfigure(errors='replace')
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seconds', type=int, default=55)
    p.add_argument('--reboot', action='store_true')
    args = p.parse_args()
    out = '/mnt/extsd/gui-boot-sequence-20261102'
    script = f'''#!/bin/sh
OUT={out}
i=0
while [ "$i" -lt 40 ]; do
    dd if=/dev/fb0 of="$OUT/frame-$i.raw" bs=307200 count=1 2>/dev/null || exit 1
    i=$((i+1))
    sleep 0.2
done
sync
echo CAPTURE_COMPLETE > "$OUT/complete"
'''
    encoded = base64.b64encode(script.encode()).decode()
    command = f'test ! -e {out} && mkdir {out} && printf %s {encoded} | /opt/cam/bin/busybox base64 -d > /tmp/gui-boot-sequence.sh; test -f /tmp/gui-boot-sequence.sh && sh /tmp/gui-boot-sequence.sh >/tmp/gui-boot-sequence.log 2>&1 </dev/null &\n'
    with serial.Serial('COM11',115200,timeout=.2) as port:
        if args.reboot:port.write(b'reboot\n')
        buf = bytearray()
        launched = False
        boot_seen = not args.reboot
        end = time.monotonic()+args.seconds
        while time.monotonic()<end:
            data = port.read(port.in_waiting or 1)
            if not data:continue
            buf.extend(data)
            print(data.decode('ascii',errors='replace'),end='',flush=True)
            if not boot_seen and (b'BOOT0' in buf or b'Booting Linux' in buf):
                boot_seen = True
                buf.clear()
            if boot_seen and not launched and b'/ # ' in buf:
                port.write(command.encode())
                launched = True
                print('\nBOOT_FRAME_CAPTURE_SENT\n',flush=True)
        print('\nCAPTURE_LAUNCHED',launched,flush=True)


if __name__ == '__main__':
    main()
