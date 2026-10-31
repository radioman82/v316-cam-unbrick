#!/bin/sh
# One-time bridge for cameras whose current SquashFS predates the SD updater.
# After a successful update, use the new read-only image and remove this bridge
# directly from the upperdir, avoiding overlay whiteouts over the new files.
[ "$1" = start ] || exit 0
if [ -x /squashfs/opt/cam/update/updater ]; then
    rm -f /overlay/upperdir/opt/cam/update/updater
    rm -f /overlay/upperdir/opt/cam/update/sd_update.sh
    rm -f /overlay/upperdir/etc/init.d/S02sdupdate
    sync
else
    /opt/cam/update/sd_update.sh start
fi
