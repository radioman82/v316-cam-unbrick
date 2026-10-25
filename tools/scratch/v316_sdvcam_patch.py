import sys
import os
import struct

STOCK_PATH = 'd:/v316cm/Firmware/firm/versuch6/_full_img_verbose.fex.extracted/squashfs-root/usr/bin/sdvcam'

# Anchors and replacements (file offsets)
PATCHES = [
    {
        'name': 'Kill USB popup thread (vaddr 0x4e29a)',
        'offset': 0x3e29a,
        'vaddr': 0x4e29a,
        'expected': bytes.fromhex('10b50446'),
        'replacement': bytes.fromhex('00207047'), # movs r0, #0; bx lr
    },
    {
        'name': 'Skip forced-popup branch (vaddr 0x4ed64)',
        'offset': 0x3ed64,
        'vaddr': 0x4ed64,
        'expected': bytes.fromhex('40f0c180'),     # bne.w 0x4eeea
        'replacement': bytes.fromhex('00f0d4b8'),  # b.w 0x4ef10
    },
    {
        'name': 'Long-press OK = poweroff (vaddr 0x5ba4e)',
        'offset': 0x4ba4e,
        'vaddr': 0x5ba4e,
        'expected': bytes.fromhex('384b40f249122e49009300232e48c0f778ec204605b0bde8f040fff7e2ba')[:26],
        'replacement': bytes.fromhex('044800bfc0f77cef09e000bf00bf00bf00bf4ff51f0000bf00bf'),
    }
]

def check(data):
    all_match = True
    print("=== CHECKING PATCH ANCHORS ===")
    for p in PATCHES:
        actual = data[p['offset']:p['offset'] + len(p['expected'])]
        match = (actual == p['expected'])
        status = "MATCH" if match else f"MISMATCH (got {actual.hex()})"
        print(f"[{status}] {p['name']} @ 0x{p['offset']:x}")
        if not match:
            all_match = False
    return all_match

def disasm(data):
    try:
        import capstone
        md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
        print("\n=== DISASSEMBLY OF PATCH SITES ===")
        for p in PATCHES:
            print(f"\n--- {p['name']} ---")
            code = data[p['offset']:p['offset'] + len(p['expected'])]
            for insn in md.disasm(code, p['vaddr']):
                print(f"  0x{insn.address:x}: {insn.mnemonic} {insn.op_str}")
    except ImportError:
        print("capstone not installed, skipping disassembly")

def apply_patches(data):
    if not check(data):
        raise ValueError("Cannot apply patches: anchor mismatch!")
    
    patched = bytearray(data)
    for p in PATCHES:
        patched[p['offset']:p['offset'] + len(p['replacement'])] = p['replacement']
    
    diff_count = sum(1 for i in range(len(data)) if data[i] != patched[i])
    print(f"\nTotal changed bytes: {diff_count} (expected: 32)")
    assert diff_count == 32, f"Expected 32 changed bytes, got {diff_count}!"
    return patched

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python v316_sdvcam_patch.py --check <input_binary>")
        print("  python v316_sdvcam_patch.py --disasm <input_binary>")
        print("  python v316_sdvcam_patch.py --apply <input_binary> <output_binary>")
        return

    mode = sys.argv[1]
    in_path = sys.argv[2] if len(sys.argv) > 2 else STOCK_PATH
    
    with open(in_path, 'rb') as f:
        data = f.read()

    if mode == '--check':
        check(data)
    elif mode == '--disasm':
        disasm(data)
    elif mode == '--apply':
        out_path = sys.argv[3] if len(sys.argv) > 3 else 'd:/v316cm/sdvcam_v7'
        patched = apply_patches(data)
        with open(out_path, 'wb') as f:
            f.write(patched)
        print(f">> Successfully written patched binary to {out_path} ({len(patched)} bytes)")
    else:
        print(f"Unknown mode: {mode}")

if __name__ == '__main__':
    main()
