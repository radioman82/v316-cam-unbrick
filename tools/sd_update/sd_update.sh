#!/bin/sh
# Once per boot, after the GUI and media mount are ready. Never source SD scripts.
BB=/opt/cam/bin/busybox
UP=/opt/cam/update/updater
PKG=/mnt/extsd/firmware-update.bin
LOCK=/tmp/v316-sd-update.lock
case "$1" in
  start)
    # Ignore HUP before forking, closing the race with init's parent exit.
    trap '' HUP
    "$BB" setsid "$0" watch >/tmp/sd-update.log 2>&1 </dev/null &
    exit 0 ;;
  watch) ;;
  prepare-test) ;;
  *) exit 2 ;;
esac
mkdir "$LOCK" 2>/dev/null || exit 0
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
echo "SD_UPDATE watcher started pid=$$"
if [ "$1" = watch ]; then
    # Let the native app finish display/USB/card initialization first.
    sleep 8
    echo 'SD_UPDATE checking media'
    # Do not flash after a late card insertion while recording.
    n=0
    while [ "$n" -lt 20 ]; do
        [ -f "$PKG" ] && "$BB" pidof sdvcam >/dev/null && break
        sleep 1
        n=$((n+1))
    done
    [ -f "$PKG" ] || { echo 'SD_UPDATE no package'; exit 0; }
fi
echo 'SD_UPDATE validating package'
"$UP" --preflight "$PKG" || exit 1
mkdir -p /tmp/v316-update
mount -t tmpfs -o size=1m tmpfs /tmp/v316-update || exit 1
cp "$UP" /tmp/v316-update/updater || exit 1
chmod 755 /tmp/v316-update/updater
MODE=--pid1
if [ "$1" = prepare-test ]; then
    MODE=--pid1-test
else
    for pid in $("$BB" pidof sdvcam); do
        for fd in /proc/$pid/fd/*; do
            case "$(readlink "$fd")" in /mnt/extsd/DCIM/*) exit 1 ;; esac
        done
    done
    # Pause the GUI while showing the independent update prompt. Resume on cancel.
    "$BB" killall -STOP sdvcam || exit 1
    /tmp/v316-update/updater --offer "$PKG"
    answer=$?
    "$BB" killall -CONT sdvcam
    [ "$answer" -eq 10 ] || exit 0
fi
# An interrupted attempt never automatically repeats on the next boot.
if [ "$MODE" = --pid1 ]; then
    [ ! -e /mnt/extsd/firmware-update.installing ] || exit 1
    mv "$PKG" /mnt/extsd/firmware-update.installing || exit 1
    PKG=/mnt/extsd/firmware-update.installing
fi
# Temporary init table: keep hardware drivers loaded, replace init with the RAM
# binary via BusyBox RESTART (SIGQUIT), which kills the other userspace processes.
printf '::restart:/tmp/v316-update/updater %s %s\n' "$MODE" "$PKG" > /tmp/v316-update/inittab
mount -o bind /tmp/v316-update/inittab /etc/inittab || exit 1
sync
kill -HUP 1 || exit 1
sleep 2
kill -QUIT 1
