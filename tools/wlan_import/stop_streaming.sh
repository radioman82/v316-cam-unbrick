#!/bin/sh
for fd in $(ls /proc/$$/fd/ 2>/dev/null); do
    [ "$fd" -gt 2 ] 2>/dev/null && eval "exec $fd>&-" 2>/dev/null
done
BB=/opt/cam/bin/busybox
sh /opt/cam/wlan/connect.sh --stop
"$BB" killall ct9000-mjpeg v316cm-mjpeg 2>/dev/null
for proc in /proc/[0-9]*; do
    args=$("$BB" tr '\000' ' ' < "$proc/cmdline" 2>/dev/null)
    case "$args" in
        *'busybox httpd -p '*' -h /opt/cam/www '*) kill "${proc##*/}" 2>/dev/null ;;
        *'busybox telnetd -p 23 -l /bin/sh '*) kill "${proc##*/}" 2>/dev/null ;;
    esac
done
"$BB" rmmod xradio_wlan 2>/dev/null
"$BB" rmmod xradio_core 2>/dev/null
"$BB" rmmod xradio_mac 2>/dev/null
exit 0
