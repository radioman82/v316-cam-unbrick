import serial, time

ser = serial.Serial('COM11', 115200, timeout=1)

# Write a clean helper script on SD card
sh_content = '''#!/bin/sh
if ! grep -q "custom_ui" /etc/init.d/S01app; then
    sed -i '/\/usr\/bin\/sdvcam/i\\    [ -d "/mnt/extsd/custom_ui" ] && mount --bind /mnt/extsd/custom_ui /usr/share/minigui/res/images\\n    [ -f "/mnt/extsd/sdvcam" ] && mount --bind /mnt/extsd/sdvcam /usr/bin/sdvcam' /etc/init.d/S01app
fi
grep -C 3 "custom_ui" /etc/init.d/S01app
'''

ser.write(b"cat << 'EOF' > /mnt/extsd/update_s01.sh\n" + sh_content.encode() + b"\nEOF\nchmod +x /mnt/extsd/update_s01.sh\n/mnt/extsd/update_s01.sh\n")
time.sleep(2)
out = ser.read_all().decode('utf-8', errors='ignore')
print(out)

ser.close()
