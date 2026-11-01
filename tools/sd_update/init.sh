#!/bin/sh
# Run after native application/device initialization, not alongside S01app.
[ "$1" = start ] || exit 0
/opt/cam/update/sd_update.sh start
