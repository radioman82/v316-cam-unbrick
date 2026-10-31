"""Wrap a private, complete 16 MiB image for the fixed V316/Fudan board.

The SD updater writes rootfs, kernel and bootlogo only. Bootloader, environment,
UDISK and the settings overlay are deliberately preserved.
"""
import argparse
import hashlib
from pathlib import Path
import struct
import zlib

MAGIC = b'V316-SDUPDATE1\n'.ljust(16, b'\0')
BOARD = b'V316-A14018-16M'.ljust(32, b'\0')
SIZE = 16 * 1024 * 1024


def build(image):
    if len(image) != SIZE:
        raise ValueError('Expected a complete 16 MiB image')
    kernel = bytearray(image[0x100000:0x400000])
    if kernel[:4] != bytes.fromhex('27051956'):
        raise ValueError('Missing uImage kernel')
    hcrc, length, dcrc = (struct.unpack_from('>I', kernel, n)[0] for n in (4, 12, 24))
    kernel[4:8] = b'\0' * 4
    if not 0 < length <= len(kernel) - 64:
        raise ValueError('Invalid kernel size')
    if zlib.crc32(kernel[:64]) != hcrc or zlib.crc32(kernel[64:64+length]) != dcrc:
        raise ValueError('Invalid uImage CRC')
    if image[0x400000:0x400004] != b'hsqs':
        raise ValueError('Missing SquashFS')
    if struct.unpack_from('<Q', image, 0x400000 + 40)[0] > 0xa80000:
        raise ValueError('Rootfs exceeds partition')
    # Require the standalone runtime and updater in the supplied build separately;
    # this wrapper cannot make an arbitrary camera image compatible.
    header = bytearray(512)
    header[:16] = MAGIC
    struct.pack_into('<I', header, 16, SIZE)
    header[20:52] = BOARD
    header[64:96] = hashlib.sha256(image).digest()
    return bytes(header) + image


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('output', type=Path, help='Private output, normally firmware-update.bin')
    args = parser.parse_args()
    args.output.write_bytes(build(args.image.read_bytes()))
    print('PACKAGE_SHA256', hashlib.sha256(args.output.read_bytes()).hexdigest())
