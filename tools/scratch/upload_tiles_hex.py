import serial, time, os

ser = serial.Serial('COM11', 115200, timeout=1)

src_dir = r"d:\v316cm\custom_ui"
tiles = [f for f in os.listdir(src_dir) if f.endswith('.png')]

# Make sure destination exists and is empty of corrupt files
ser.write(b"mkdir -p /mnt/extsd/custom_ui\n")
time.sleep(0.5)
ser.read_all()

for tile in tiles:
    local_p = os.path.join(src_dir, tile)
    with open(local_p, 'rb') as f:
        data = f.read()
    
    remote_p = f"/mnt/extsd/custom_ui/{tile}"
    ser.write(f"> {remote_p}\n".encode())
    time.sleep(0.05)
    
    # 128-byte chunks
    chunk_size = 128
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        hex_str = ''.join(f'\\x{b:02x}' for b in chunk)
        cmd = f"printf '{hex_str}' >> {remote_p}\n"
        ser.write(cmd.encode())
        time.sleep(0.03)
    
    print(f"Uploaded {tile}: {len(data)} bytes")

time.sleep(0.5)
ser.write(b"ls -lh /mnt/extsd/custom_ui/*.png\n")
time.sleep(1)
out = ser.read_all().decode('utf-8', errors='ignore')
print(out)

ser.close()
print("All tiles uploaded successfully!")
