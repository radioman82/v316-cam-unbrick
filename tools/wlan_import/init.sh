#!/bin/sh
[ "$1" = start ] || exit 0
trap '' HUP
/opt/cam/bin/busybox setsid /opt/cam/wlan/import.sh > /tmp/wlan-import.log 2>&1 </dev/null &
exit 0
