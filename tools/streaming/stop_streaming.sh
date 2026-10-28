#!/bin/sh
# Close the GUI's inherited media descriptors before starting any background work.
for fd in $(ls /proc/$$/fd/ 2>/dev/null); do
    [ "$fd" -gt 2 ] 2>/dev/null && eval "exec $fd>&-" 2>/dev/null
done
rm -f /tmp/v316cm-stream-ready
killall v316cm-mjpeg wpa_supplicant hostapd udhcpd 2>/dev/null
# BusyBox daemons may have comm=busybox; identify our exact applet arguments.
for proc in /proc/[0-9]*; do
    args=$(tr '\000' ' ' < "$proc/cmdline" 2>/dev/null)
    case "$args" in
        *'busybox httpd -p '*' -h /mnt/extsd/www '*) kill "${proc##*/}" 2>/dev/null ;;
        *'busybox telnetd -p 23 -l /bin/sh '*) kill "${proc##*/}" 2>/dev/null ;;
    esac
done
ifconfig wlan0 0.0.0.0 down 2>/dev/null
rmmod xradio_wlan 2>/dev/null
rmmod xradio_core 2>/dev/null
rmmod xradio_mac 2>/dev/null
exit 0
