#!/bin/sh
# BusyBox udhcpc lease hook. No lease values are evaluated as shell code.
umask 077
BB=/opt/cam/bin/busybox
TOOL=/opt/cam/wlan/wlan-import
RUN=/run/v316-wlan
[ "$interface" = wlan0 ] || exit 1
case "$1" in
    deconfig)
        rm -f "$RUN/ip"
        "$BB" ifconfig wlan0 0.0.0.0
        ;;
    bound|renew)
        "$TOOL" --valid-ip "$ip" || exit 1
        "$TOOL" --valid-ip "$subnet" || exit 1
        case "$ip" in 0.*|127.*|169.254.*) exit 1 ;; esac
        "$BB" ifconfig wlan0 "$ip" netmask "$subnet" up || exit 1
        "$BB" route del default dev wlan0 2>/dev/null
        for gw in $router; do
            "$TOOL" --valid-ip "$gw" || continue
            "$BB" route add default gw "$gw" dev wlan0 && break
        done
        : > "$RUN/resolv.conf"
        for ns in $dns; do
            "$TOOL" --valid-ip "$ns" && printf 'nameserver %s\n' "$ns" >> "$RUN/resolv.conf"
        done
        printf '%s\n' "$ip" > "$RUN/ip.new"
        mv "$RUN/ip.new" "$RUN/ip"
        ;;
esac
exit 0
