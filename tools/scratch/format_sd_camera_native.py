import serial
import time

ser = serial.Serial('COM11', 115200, timeout=1.0)
ser.reset_input_buffer()

print("1. Unmounting SD card...")
ser.write(b"umount /mnt/extsd\n")
time.sleep(1.0)

print("2. Formatting SD card with exact Allwinner camera specs...")
format_cmd = "/usr/bin/newfs_msdos -L UDISK -c 128 -b 65536 -O allwinner -n 2 -F 32 /dev/mmcblk0p1\n"
ser.write(format_cmd.encode('utf-8'))
time.sleep(3.0)

print("3. Remounting and creating camera directory structure...")
setup_cmd = """mount -t vfat /dev/mmcblk0p1 /mnt/extsd
mkdir -p /mnt/extsd/DCIM
mkdir -p /mnt/extsd/.data
sync
df -h /mnt/extsd
ls -la /mnt/extsd
"""
ser.write(setup_cmd.encode('utf-8'))
time.sleep(1.5)

out = b''
for _ in range(30):
    if ser.in_waiting:
        out += ser.read(ser.in_waiting)
        time.sleep(0.05)

print("Format output:\n", out.decode('utf-8', errors='replace'))

print("4. Rebooting camera cleanly...")
ser.write(b"sync; reboot\n")
time.sleep(1.0)
ser.close()
print("Camera reboot triggered!")
