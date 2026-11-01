#!/bin/sh
# Late, once-per-boot import; firmware updates have priority. No late SD polling.
sleep 10
[ -f /mnt/extsd/wlan.conf ] || exit 0
n=0
while [ -d /tmp/v316-sd-update.lock ] || [ -d /tmp/v316cm-network-lock ]; do
    [ "$n" -lt 50 ] || exit 0
    [ ! -f /mnt/extsd/firmware-update.bin ] || exit 0
    sleep 1
    n=$((n+1))
done
[ ! -f /mnt/extsd/firmware-update.bin ] || exit 0
exec /opt/cam/wlan/wlan-import --import /mnt/extsd/wlan.conf /data/wlan.conf
