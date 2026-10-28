#!/bin/sh
# Serialized reconciliation of the latest GUI mode, including rapid tile changes.
for fd in $(ls /proc/$$/fd/ 2>/dev/null); do
    [ "$fd" -gt 2 ] 2>/dev/null && eval "exec $fd>&-" 2>/dev/null
done
lock=/tmp/v316cm-network-lock
mkdir "$lock" 2>/dev/null || exit 0
trap 'rmdir "$lock" 2>/dev/null' EXIT
while :; do
    if [ -f /tmp/v316cm-stream-mode ]; then
        applied=stream
        V316CM_MANAGED_STREAM=1 sh /mnt/extsd/start_streaming.sh
    else
        applied=camera
        sh /mnt/extsd/stop_streaming.sh
    fi
    desired=camera
    [ -f /tmp/v316cm-stream-mode ] && desired=stream
    [ "$desired" = "$applied" ] || continue
    rmdir "$lock"
    trap - EXIT
    # A request racing with unlock either starts its own worker or is caught here.
    desired=camera
    [ -f /tmp/v316cm-stream-mode ] && desired=stream
    [ "$desired" = "$applied" ] && exit 0
    mkdir "$lock" 2>/dev/null || exit 0
    trap 'rmdir "$lock" 2>/dev/null' EXIT
done
