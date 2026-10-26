#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
keys.py -- Tastenpruefstand fuer die V316CM.

Holt die evdev-Mitschnitte von der SD-Karte und decodiert sie zu einer
lesbaren Tabelle: welche Taste, wie lange gehalten, prellt sie, kommt sie an.

Aufruf:
    python keys.py            # auswerten
    python keys.py --reset    # Mitschnitte leeren (vor einer neuen Messung)
"""
import subprocess, sys, os, struct

DEV = {
    0: ('event0', 'sunxi-gpadc0  (ADC-Leiter: Seite)'),
    1: ('event1', 'axp22x-powerkey (PMIC: Front/OK)'),
    2: ('event2', 'gpiokey'),
    3: ('event3', 'sunchip-gpioirkey (IR)'),
}

# Kernel-Codes, die auf diesem Geraet vorkommen koennen
CODE = {
    28:  'KEY_ENTER',
    60:  'IR-Taste',
    61:  'IR-Taste',
    62:  'IR-Taste',
    102: 'KEY_HOME',
    107: 'KEY_END',
    114: 'KEY_VOLUMEDOWN  (Seite runter)',
    115: 'KEY_VOLUMEUP    (Seite hoch)',
    116: 'KEY_POWER       (Front/OK)',
    139: 'KEY_MENU',
}

PY = r'D:\Phyton\python.exe'
SH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sh.py')


def dev(cmd, wait=3.0):
    p = subprocess.run([PY, SH, '--wait', str(wait), cmd],
                       capture_output=True, text=True)
    return p.stdout


def fetch():
    out = dev('for d in 0 1 2 3; do echo "==D$d"; od -An -tx4 -w16 -v '
              '/mnt/extsd/dbg/e$d.bin; done', 5.0)
    data, cur = {}, None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith('==D'):
            cur = int(line[3:])
            data[cur] = []
            continue
        if cur is None:
            continue
        parts = line.split()
        if len(parts) != 4:
            continue
        try:
            w = [int(x, 16) for x in parts]
        except ValueError:
            continue
        sec, usec, tc, val = w
        typ = tc & 0xFFFF
        code = (tc >> 16) & 0xFFFF
        data[cur].append((sec + usec / 1e6, typ, code,
                          struct.unpack('<i', struct.pack('<I', val))[0]))
    return data


def analyse(evs):
    """Liefert (Druecke, Preller, Autorepeat)."""
    presses, bounce, repeat = [], 0, 0
    down = {}
    for ts, typ, code, val in evs:
        if typ != 1:
            continue
        if val == 1:
            if code in down:      # zweites DOWN ohne UP dazwischen
                bounce += 1
            down[code] = ts
        elif val == 2:
            repeat += 1
        elif val == 0 and code in down:
            t0 = down.pop(code)
            presses.append((code, t0, ts - t0))
    for code, t0 in down.items():   # nie losgelassen
        presses.append((code, t0, None))
    return presses, bounce, repeat


def main():
    if '--reset' in sys.argv:
        dev('for d in 0 1 2 3; do : > /mnt/extsd/dbg/e$d.bin; done; echo OK', 3.0)
        print('Mitschnitte geleert.')
        return

    data = fetch()
    total = 0
    t0 = None
    for idx in sorted(DEV):
        for ev in data.get(idx, []):
            if t0 is None or ev[0] < t0:
                t0 = ev[0]
    for idx in sorted(DEV):
        fname, label = DEV[idx]
        evs = data.get(idx, [])
        presses, bounce, repeat = analyse(evs)
        total += len(presses)
        print('\n%s  %s' % (fname, label))
        print('  %d Ereignisse, %d Druecke' % (len(evs), len(presses)))
        for i, (code, t0p, dur) in enumerate(presses, 1):
            name = CODE.get(code, 'Code %d' % code)
            rel = (t0p - t0) if t0 is not None else 0.0
            if dur is None:
                print('  #%d  t=%7.2fs  %-34s  NICHT LOSGELASSEN'
                      % (i, rel, name))
            else:
                print('  #%d  t=%7.2fs  %-34s  %6.1f ms'
                      % (i, rel, name, dur * 1000))
        if bounce:
            print('  !! %d Preller (mehrere DOWN ohne UP)' % bounce)
        if repeat:
            print('     %d Autorepeat-Ereignisse' % repeat)
    if total == 0:
        print('\nKein einziger Tastendruck aufgezeichnet.')
    print()


if __name__ == '__main__':
    main()
