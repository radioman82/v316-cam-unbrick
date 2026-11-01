#!/bin/sh
# Internal runtime: shared, data-only network configuration and DHCP support.
for fd in $(ls /proc/$$/fd/ 2>/dev/null); do
    [ "$fd" -gt 2 ] 2>/dev/null && eval "exec $fd>&-" 2>/dev/null
done
BB=/opt/cam/bin/busybox
TOOL=/opt/cam/wlan/wlan-import
RUN=/run/v316-wlan
still_selected() { [ "$V316CM_MANAGED_STREAM" != 1 ] || [ -f /tmp/v316cm-stream-mode ]; }
sleep 2
still_selected || exit 0
PORT=$("$TOOL" --get /data/wlan.conf http_port) || exit 1
if ! "$TOOL" --same /data/wlan.conf "$RUN/active.conf" 2>/dev/null ||
   ! /usr/sbin/wpa_cli -p /var/run/wpa_supplicant -i wlan0 status 2>/dev/null | "$BB" grep -q '^wpa_state=COMPLETED$'; then
    sh /opt/cam/wlan/connect.sh /data/wlan.conf || exit 1
fi
still_selected || exit 0
if ! "$BB" netstat -ltn 2>/dev/null | "$BB" grep -q ":$PORT "; then
    "$BB" killall httpd 2>/dev/null
    "$BB" httpd -p "$PORT" -h /opt/cam/www || exit 1
fi
if ! "$BB" netstat -ltn 2>/dev/null | "$BB" grep -q ':23 '; then
    "$BB" telnetd -p 23 -l /bin/sh || exit 1
fi
touch /tmp/v316cm-stream-ready
echo 'WLAN AND STREAM READY' >> /tmp/streaming.log
