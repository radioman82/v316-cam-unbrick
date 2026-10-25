import serial, time, os

ser = serial.Serial('COM11', 115200, timeout=1)

with open(r'd:\v316cm\zh-DE_clean.xml', 'rb') as f:
    data = f.read()

remote_p = "/mnt/extsd/zh-DE.xml"
ser.write(f"> {remote_p}\n".encode())
time.sleep(0.1)

chunk_size = 256
for i in range(0, len(data), chunk_size):
    chunk = data[i:i+chunk_size]
    hex_str = ''.join(f'\\x{b:02x}' for b in chunk)
    cmd = f"printf '{hex_str}' >> {remote_p}\n"
    ser.write(cmd.encode())
    time.sleep(0.04)

time.sleep(0.5)
# Copy over rootfs
ser.write(b"cp /mnt/extsd/zh-DE.xml /usr/share/minigui/res/lang/zh-DE.xml && echo XML_COPIED_OK\n")
time.sleep(1)
out = ser.read_all().decode('utf-8', errors='ignore')
print(out)

ser.close()
print("Uploaded and activated clean German XML!")
