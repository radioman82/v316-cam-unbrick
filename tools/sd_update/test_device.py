"""Non-destructive package rejection tests on an already staged camera.

Requires /tmp/v316-updater and /mnt/extsd/firmware-update.bin. Never starts
the PID-1 writer. Evidence stays in the private work directory.
"""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from camera_uart import CameraUART


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence', type=Path, required=True)
    args = p.parse_args()
    c = CameraUART()
    report = {}
    target = '/mnt/extsd/v316-update-test-invalid.bin'
    source = '/mnt/extsd/firmware-update.bin'
    runner = '/tmp/v316-updater'
    try:
        before = c.run(f'{c.busybox} sha256sum /dev/mtdblock0 /dev/mtdblock1 /dev/mtdblock2 /dev/mtdblock4 /dev/mtdblock5 /dev/mtdblock6', timeout=45)
        report['preflight'] = c.run(f'{runner} --preflight {source}', timeout=30)
        tests = [
            ('truncated', f'dd if={source} of={target} bs=512 count=1 2>/dev/null', 'PAKETGROESSE UNGUELTIG'),
            ('wrong_model', f'cp {source} {target}; printf X | dd of={target} bs=1 seek=20 conv=notrunc 2>/dev/null', 'FALSCHES PAKETMODELL'),
            ('corrupt_payload', f'cp {source} {target}; printf X | dd of={target} bs=1 seek=512 conv=notrunc 2>/dev/null', 'SHA256 PRUEFSUMME FALSCH'),
            ('unknown_version', f'cp {source} {target}; printf X | dd of={target} bs=1 seek=96 conv=notrunc 2>/dev/null', 'PAKETVERSION UNBEKANNT'),
        ]
        for name, fixture, expected in tests:
            c.run(fixture, timeout=30)
            try:
                c.run(f'{runner} --check {target}', timeout=30)
            except RuntimeError as e:
                assert expected in str(e), str(e)
                report[name] = str(e)
                print(name, 'PASS', flush=True)
            else:
                raise AssertionError(f'{name} unexpectedly accepted')
        # A normal process can never invoke the writing phase, even with a valid file.
        try:
            c.run(f'{runner} --pid1 {source}', timeout=5)
        except RuntimeError as e:
            assert 'PID 1 ERFORDERLICH' in str(e)
            report['pid1_guard'] = str(e)
        else:
            raise AssertionError('PID 1 guard missing')
        after = c.run(f'{c.busybox} sha256sum /dev/mtdblock0 /dev/mtdblock1 /dev/mtdblock2 /dev/mtdblock4 /dev/mtdblock5 /dev/mtdblock6', timeout=45)
        assert before == after, 'Flash changed during rejection tests'
        report['flash_before_after'] = before
        report['flash_unchanged'] = True
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(report, indent=2), encoding='utf-8')
        print('REJECTION_TESTS_PASS_FLASH_UNCHANGED', flush=True)
    finally:
        c.run(f'rm -f {target}')
        c.close()


if __name__ == '__main__':
    main()
