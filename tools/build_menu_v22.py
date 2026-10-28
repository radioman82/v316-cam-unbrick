"""Reproduce the camera's v21, then add grouped modes and web control key hooks."""
import hashlib
from pathlib import Path
import struct
import subprocess
import tempfile
from thumb import enc_bl as bl, enc_bw as bw

ROOT = Path(__file__).resolve().parents[1]
TOOL = Path(r"C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin")


def main():
    data = bytearray((ROOT / 'firmware/sdvcam/sdvcam_v8').read_bytes())
    assert hashlib.md5(data).hexdigest() == 'ee7425e348fc3d35d09ff62fc405860a'
    # Exact v21, the live baseline at the start of this change.
    dispatcher = bytes.fromhex('30b504461546032d13d0d4f814010ef0ddfb0422002d00d000222046fff7aafd022d05d143f2a220c0f22000c1f79eec30bd20460121fff749ff30bd').ljust(80, b'\0')
    data[0x4afe0:0x4b030] = dispatcher
    data[0x1f32a2:0x1f32c2] = b'/mnt/extsd/start_streaming.sh &\0'
    data[0x23ad70:0x23ad82] = bytes.fromhex('204605b0bde8f040d0f814010368db6e1847')
    data[0x4bc90:0x4bc94] = bytes.fromhex('eff16eb8')
    assert hashlib.md5(data).hexdigest() == '4154e8520e13711bc70fe9e65d424ec7'
    with tempfile.TemporaryDirectory() as work:
        work = Path(work)
        obj, elf, raw = (work / n for n in ('patch.o', 'patch.elf', 'patch.bin'))
        subprocess.run([str(TOOL / 'arm-none-eabi-as.exe'), '-mthumb', '-o', str(obj), str(ROOT / 'tools/patches/menu_v22.s')], check=True)
        subprocess.run([str(TOOL / 'arm-none-eabi-ld.exe'), '-Ttext=0', '-o', str(elf), str(obj)], check=True)
        subprocess.run([str(TOOL / 'arm-none-eabi-objcopy.exe'), '-O', 'binary', str(elf), str(raw)], check=True)
        symbols = {}
        for line in subprocess.check_output([str(TOOL / 'arm-none-eabi-nm.exe'), str(elf)], text=True).splitlines():
            parts = line.split()
            if len(parts) == 3:
                symbols[parts[2]] = int(parts[0], 16)
        raw_data = raw.read_bytes()
        code = raw_data[0x24ad84:]
        front_code = raw_data[0x5afe4:0x5b030]
    print('Cave bytes:', len(code))
    assert data[0x23ad84:0x23ad84 + len(code)] == bytes(len(code))
    data[0x23ad84:0x23ad84 + len(code)] = code
    def patch(address, expected, replacement):
        offset = address - 0x10000
        assert data[offset:offset + len(expected)] == expected, hex(address)
        assert len(expected) == len(replacement)
        data[offset:offset + len(replacement)] = replacement
    patch(0x5afe0, dispatcher[:4], bw(0x5afe0, symbols['tile_dispatch']))
    patch(0x5afe4, dispatcher[4:], front_code)
    patch(0x5b83c, bytes.fromhex('f0b585b0'), bw(0x5b83c, symbols['remote_key']))
    patch(0x5bc0e, bytes.fromhex('fef7fbfe'), bl(0x5bc0e, symbols['show_modes']))
    patch(0x5bc90, bytes.fromhex('eff16eb8'), bw(0x5bc90, symbols['front_toggle']))
    patch(0x675e4, bytes.fromhex('9b6e9847'), bl(0x675e4, symbols['filter_modes']))
    patch(0x66dc4, bytes.fromhex('38b50446'), bw(0x66dc4, symbols['select_local_mode']))
    patch(0x5c9d4, struct.pack('<I', 0x5ab55), struct.pack('<I', symbols['mode_callback'] | 1))
    # Constructor initializes bool 0x11c and the adjacent family byte 0x11d.
    patch(0x676a2, bytes.fromhex('84f81c51'), bytes.fromhex('a4f81c51'))
    output = ROOT / 'firmware/sdvcam/sdvcam_menu_v22'
    output.write_bytes(data)
    print(output, 'MD5', hashlib.md5(data).hexdigest())
    print('Symbols:', {key: hex(symbols[key]) for key in ('tile_dispatch', 'remote_key', 'dismiss_prompt', 'filter_modes', 'mode_callback')})


if __name__ == '__main__':
    main()
