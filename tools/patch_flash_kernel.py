import struct
import subprocess
import zlib
import os

def main():
    print("=== Step 1: Loading extracted vmlinux.bin ===")
    with open('vmlinux.bin', 'rb') as f:
        vmlinux = bytearray(f.read())
    
    # Verify Winbond ID at 0x51d2d4
    winbond_id = vmlinux[0x51d2d4:0x51d2d7]
    print(f"Original ID at 0x51d2d4: {winbond_id.hex()} (expected ef4018)")
    assert winbond_id == b'\xef\x40\x18', f"Unexpected bytes: {winbond_id.hex()}"
    
    # Patch to Fudan Micro FM25Q128 (a1 40 18)
    vmlinux[0x51d2d4] = 0xa1
    print(f"Patched ID at 0x51d2d4: {vmlinux[0x51d2d4:0x51d2d7].hex()} (a14018)")
    
    patched_vmlinux_file = 'vmlinux_fudan_patched.bin'
    with open(patched_vmlinux_file, 'wb') as f:
        f.write(vmlinux)
    print(f"Saved {patched_vmlinux_file} ({len(vmlinux)} bytes)")
    
    print("\n=== Step 2: Compressing with 7-Zip ===")
    gz_out = 'vmlinux_fudan.gz'
    if os.path.exists(gz_out):
        os.remove(gz_out)
        
    seven_zip = r"C:\Program Files\7-Zip\7z.exe"
    cmd = [seven_zip, "a", "-tgzip", "-mx=9", "-mfb=258", "-mpass=15", gz_out, patched_vmlinux_file]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"7z failed: {res.stderr}")
    
    with open(gz_out, 'rb') as f:
        compressed_gz = f.read()
    print(f"Compressed gzip size: {len(compressed_gz)} bytes")
    
    target_len = 3019821
    pad_needed = target_len - len(compressed_gz)
    print(f"Target length: {target_len}, Padding needed: {pad_needed} bytes")
    assert pad_needed >= 0, f"Compressed size {len(compressed_gz)} exceeds target {target_len}!"
    
    padded_gz = compressed_gz + (b'\x00' * pad_needed)
    assert len(padded_gz) == target_len
    
    print("\n=== Step 3: Reassembling zImage ===")
    with open('Firmware/full_img.fex', 'rb') as f:
        f.seek(0x100040)
        orig_zimage = f.read(3036544)
        
    stub = orig_zimage[:0x4117]
    tail = orig_zimage[0x2e5544:] # 60 bytes
    
    new_zimage = stub + padded_gz + tail
    print(f"New zImage length: {len(new_zimage)} (expected 3036544)")
    assert len(new_zimage) == 3036544
    
    print("\n=== Step 4: Building uImage Header ===")
    with open('Firmware/full_img.fex', 'rb') as f:
        f.seek(0x100000)
        orig_uimage_hdr = bytearray(f.read(64))
        
    data_crc = zlib.crc32(new_zimage) & 0xffffffff
    print(f"New data CRC32: {hex(data_crc)}")
    
    # Put data CRC into header at bytes 24..27
    struct.pack_into('>I', orig_uimage_hdr, 24, data_crc)
    
    # Zero out header CRC at bytes 4..7 before recalculating
    struct.pack_into('>I', orig_uimage_hdr, 4, 0)
    
    # Recalculate header CRC
    hdr_crc = zlib.crc32(orig_uimage_hdr) & 0xffffffff
    print(f"New header CRC32: {hex(hdr_crc)}")
    struct.pack_into('>I', orig_uimage_hdr, 4, hdr_crc)
    
    new_uimage = orig_uimage_hdr + new_zimage
    with open('kernel_fudan_patched.uImage', 'wb') as f:
        f.write(new_uimage)
    print(f"Saved standalone kernel_fudan_patched.uImage ({len(new_uimage)} bytes)")
    
    print("\n=== Step 5: Creating full_img_fudan_patched.fex ===")
    with open('Firmware/full_img.fex', 'rb') as f:
        full_img = bytearray(f.read())
        
    # Inject new uImage at offset 0x100000
    full_img[0x100000 : 0x100000 + len(new_uimage)] = new_uimage
    
    out_fex = 'Firmware/full_img_fudan_patched.fex'
    with open(out_fex, 'wb') as f:
        f.write(full_img)
    print(f"SUCCESS! Created {out_fex} ({len(full_img)} bytes)")

if __name__ == '__main__':
    main()
