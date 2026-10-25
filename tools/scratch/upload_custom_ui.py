import serial, time, os, base64

ser = serial.Serial('COM11', 115200, timeout=1)

# Step 1: Ensure directory and copy original images on device
setup_cmd = (
    "mkdir -p /mnt/extsd/custom_ui\n"
    "cp -n /usr/share/minigui/res/images/* /mnt/extsd/custom_ui/ 2>/dev/null\n"
    "echo SETUP_DONE\n"
)
ser.write(setup_cmd.encode())
time.sleep(2)
out = ser.read_all().decode('utf-8', errors='ignore')
print(out)

# Step 2: Upload each custom tile
src_dir = r"d:\v316cm\custom_ui"
tiles = [f for f in os.listdir(src_dir) if f.endswith('.png')]

for tile in tiles:
    local_p = os.path.join(src_dir, tile)
    with open(local_p, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode('ascii')
    
    # Send to device
    print(f"Uploading {tile} ({len(data)} bytes)...")
    ser.write(f"echo '{b64}' | base64 -d > /mnt/extsd/custom_ui/{tile}\n".encode())
    time.sleep(0.3)
    resp = ser.read_all().decode('utf-8', errors='ignore')
    if "error" in resp.lower():
        print("  Error:", resp)

# Verify
ser.write(b"ls -l /mnt/extsd/custom_ui/function_*.png\n")
time.sleep(1)
out = ser.read_all().decode('utf-8', errors='ignore')
print(out)

ser.close()
print("Upload completed!")
