#!/bin/sh
# Diagnostic only: preserve framebuffer samples on SD across real power-off.
OUT=/mnt/extsd/shutdown-check-20261102-1
i=0
while [ "$i" -lt 30 ]; do
    dd if=/dev/fb0 of="$OUT/frame-$i.raw" bs=307200 count=1 2>/dev/null || exit 1
    sync
    i=$((i+1))
    sleep 0.2
done
