import serial
import time

ser = serial.Serial('COM11', 115200, timeout=1.0)
ser.reset_input_buffer()

cmd = """cat << 'EOF' > /etc/udev/rules.d/10-local.rules
ACTION!="add", GOTO="aw"
KERNEL=="sd[a-z]",           SUBSYSTEM=="block", ENV{NPARTS}=="0",    RUN+="/usr/bin/udev_handler add udisk /dev/%k"
KERNEL=="sd[a-z][0-9]",      SUBSYSTEM=="block", ENV{PARTN}=="[1-9]", RUN+="/usr/bin/udev_handler add udisk /dev/%k"
KERNEL=="mmcblk[0-9]*",      SUBSYSTEM=="block", RUN+="/usr/bin/udev_handler add sd /dev/mmcblk0"
LABEL="aw"

ACTION!="remove", GOTO="aw"
KERNEL=="sd[a-z]*",     SUBSYSTEM=="block", RUN+="/usr/bin/udev_handler remove udisk"
KERNEL=="mmcblk[0-9]*", SUBSYSTEM=="block", RUN+="/usr/bin/udev_handler remove sd"
LABEL="aw"

ACTION!="change", GOTO="aw"
KERNEL=="hdmi", SUBSYSTEM=="extcon", ATTR{state}=="HDMI=1", RUN+="/usr/bin/udev_handler add hdmi"
KERNEL=="hdmi", SUBSYSTEM=="extcon", ATTR{state}=="HDMI=0", RUN+="/usr/bin/udev_handler remove hdmi"
KERNEL=="cvbs", SUBSYSTEM=="extcon", ATTR{state}=="1", RUN+="/usr/bin/udev_handler add cvbs"
KERNEL=="cvbs", SUBSYSTEM=="extcon", ATTR{state}=="0", RUN+="/usr/bin/udev_handler remove cvbs"
LABEL="aw"

ACTION!="change", GOTO="gadget"
KERNEL=="android0", SUBSYSTEM=="android_usb", ATTR{state}=="CONFIGURED", RUN+="/usr/bin/udev_handler add usb2host"
KERNEL=="android0", SUBSYSTEM=="android_usb", ATTR{state}=="DISCONNECTED", RUN+="/usr/bin/udev_handler remove usb2host"
LABEL="gadget"
EOF
sync
reboot
"""
ser.write(cmd.encode('utf-8'))
time.sleep(1.0)
ser.close()
print("Camera rebooting with perfect SD card setup!")
