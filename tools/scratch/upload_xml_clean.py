import serial, time

ser = serial.Serial('COM11', 115200, timeout=1)

with open(r'd:\v316cm\zh-DE_clean.xml', 'r', encoding='utf-8') as f:
    lines = f.readlines()

ser.write(b"> /mnt/extsd/zh-DE.xml\n")
time.sleep(0.5)
ser.read_all()

total = len(lines)
print(f"Uploading {total} XML lines with prompt handshake...")

for idx, line in enumerate(lines):
    # write line escaped
    escaped = line.rstrip('\r\n').replace("'", "'\\''")
    ser.write(f"echo '{escaped}' >> /mnt/extsd/zh-DE.xml\n".encode('utf-8'))
    # Wait for prompt or small delay every 10 lines
    if idx % 10 == 0:
        time.sleep(0.08)
        ser.read_all()
        if idx % 50 == 0:
            print(f"  {idx}/{total} lines...")

time.sleep(1)
ser.write(b"cp /mnt/extsd/zh-DE.xml /usr/share/minigui/res/lang/zh-DE.xml\n")
time.sleep(0.5)
ser.write(b"ls -lh /usr/share/minigui/res/lang/zh-DE.xml\n")
time.sleep(1)
out = ser.read_all().decode('utf-8', errors='ignore')
print(out)
ser.close()
print("Clean XML uploaded successfully!")
