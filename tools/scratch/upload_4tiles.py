import os, base64, serial, time

ser = serial.Serial('COM11', 115200, timeout=1)

src_dir = r"d:\v316cm\custom_ui"
tiles = ["function_mode.png", "function_media.png", "function_setting.png", "function_return.png"]

def run_cmd(cmd):
    ser.write(cmd.encode() + b"\n")
    time.sleep(0.1)
    out = b""
    while ser.in_waiting:
        out += ser.read(ser.in_waiting)
        time.sleep(0.02)
    return out.decode("utf-8", errors="replace")

for tile in tiles:
    lp = os.path.join(src_dir, tile)
    with open(lp, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("ascii")
    
    print(f"Uploading {tile} ({len(data)} bytes)...")
    run_cmd(f"rm -f /tmp/tile.b64")
    
    chunk_sz = 200
    for i in range(0, len(b64), chunk_sz):
        c = b64[i:i+chunk_sz]
        run_cmd(f"echo -n '{c}' >> /tmp/tile.b64")
    
    run_cmd(f"base64 -d /tmp/tile.b64 > /mnt/extsd/custom_ui/{tile}")
    run_cmd("sync")

print("\nVerifying uploaded files on camera:")
print(run_cmd("ls -l /mnt/extsd/custom_ui/function_*.png"))

ser.close()
print("Done!")
