import zlib, struct

# Let's read the first 1024 bytes of mtdblock4
# We know the first 4 bytes are CRC32
# Let's test standard U-Boot crc
with open('d:/v316cm/env_sample.bin', 'rb') as f:
    data = f.read()

stored_crc = struct.unpack('<I', data[:4])[0]
print("Stored CRC:", hex(stored_crc))

# U-boot env size for NOR flash is usually the partition size or defined in config
# Let's find the exact data slice that produces stored_crc
for size in [0x10000, 0x20000, len(data)]:
    c = zlib.crc32(data[4:size]) & 0xffffffff
    print(f"CRC(4..{hex(size)}): {hex(c)}")
    c_red = zlib.crc32(data[5:size]) & 0xffffffff
    print(f"CRC(5..{hex(size)}): {hex(c_red)}")
