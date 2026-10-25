with open(r'd:\v316cm\Firmware\firm\versuch6\_full_img_verbose.fex.extracted\squashfs-root\usr\lib\libminigui_ths-3.0.so.12.0.0', 'rb') as f:
    data = f.read()

import struct

def vma_to_file(vma):
    if vma >= 0x8c4ec: return vma - 0x8c4ec + 0x7c4ec
    return vma

table_file = vma_to_file(0x97e54)

def read_str(vma):
    off = vma_to_file(vma)
    end = data.find(b'\x00', off)
    return data[off:end].decode('latin1', errors='ignore')

print("Index | Default Linux Code | Name Pointer -> Name | MiniGUI Scancode")
print("-" * 70)
for i in range(10):
    entry = table_file + i * 12
    linux_code, name_ptr, mg_scancode = struct.unpack('<III', data[entry:entry+12])
    print(f"{i:5} | {linux_code:18} | {name_ptr:#x} -> {read_str(name_ptr):10} | {mg_scancode} ({hex(mg_scancode)})")
