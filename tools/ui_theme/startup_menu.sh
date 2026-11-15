#!/bin/sh
# Finish the boot menu using the existing camera menu control after late paints.
# S01app starts this once; do not poll/reopen the menu during normal operation.
BB=/opt/cam/bin/busybox
CONTROL=/opt/cam/bin/ct9000-control
n=0
while [ "$n" -lt 30 ]; do
    pid=$("$BB" pidof sdvcam)
    case "$pid" in
        ''|*[!0-9]*) ;;
        *)
            if [ -f "/tmp/v316cm-tiles-done-$pid" ]; then
                # The native startup audio wait and late preview paints finish
                # after the early tile Show(). Re-enter through menu control.
                sleep 3
                [ "$("$BB" pidof sdvcam)" = "$pid" ] || exit 1
                # An early physical key is the user's navigation, not boot work.
                if "$BB" grep -q 'MSG_KEYDOWN' /tmp/sdvcam.log; then
                    echo 'BOOT_MENU skipped: user already used a key'
                    exit 0
                fi
                echo "BOOT_MENU ready pid=$pid"
                "$CONTROL" menu
                exit $?
            fi
            ;;
    esac
    n=$((n+1))
    sleep 1
done
echo 'BOOT_MENU timeout waiting for native initialization'
exit 1
