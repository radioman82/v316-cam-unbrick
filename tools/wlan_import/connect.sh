#!/bin/sh
# Data comes only from wlan-import; never source/eval a WLAN configuration.
umask 077
BB=/opt/cam/bin/busybox
TOOL=/opt/cam/wlan/wlan-import
RUN=/run/v316-wlan
mkdir -p "$RUN" /var/run/wpa_supplicant || exit 1
stop_client() {
    if [ -f "$RUN/udhcpc.pid" ]; then
        read -r pid < "$RUN/udhcpc.pid"
        case "$pid" in ''|*[!0-9]*) ;; *) "$BB" kill "$pid" 2>/dev/null ;; esac
    fi
    "$BB" killall wpa_supplicant hostapd udhcpd 2>/dev/null
    rm -f "$RUN/udhcpc.pid" "$RUN/ip" "$RUN/active.conf" /tmp/v316cm-stream-ready
    "$BB" ifconfig wlan0 0.0.0.0 down 2>/dev/null
    return 0
}
fail() { printf '%s\n' "$1" > "$RUN/error"; exit 1; }
if [ "$1" = --stop ]; then stop_client; exit 0; fi
CFG=$1
"$TOOL" --normalize "$CFG" "$RUN/candidate.conf" || fail CONFIG
"$TOOL" --wpa "$RUN/candidate.conf" "$RUN/wpa.conf" || fail CONFIG
MODE=$("$TOOL" --get "$RUN/candidate.conf" ip_mode) || fail CONFIG
rm -f "$RUN/error"
stop_client
if ! "$BB" lsmod | "$BB" grep -q xradio_wlan; then
    "$BB" insmod /lib/modules/4.9.118/xradio_mac.ko 2>/dev/null
    "$BB" insmod /lib/modules/4.9.118/xradio_core.ko 2>/dev/null
    "$BB" insmod /lib/modules/4.9.118/xradio_wlan.ko 2>/dev/null
    sleep 1
fi
"$BB" ifconfig wlan0 up || fail DRIVER
LD_LIBRARY_PATH=/opt/cam/lib:$LD_LIBRARY_PATH /opt/cam/bin/wpa_supplicant \
    -B -i wlan0 -c "$RUN/wpa.conf" -P "$RUN/wpa.pid" > "$RUN/supplicant.log" 2>&1 || fail DRIVER
n=0
while [ "$n" -lt 25 ]; do
    /usr/sbin/wpa_cli -p /var/run/wpa_supplicant -i wlan0 status 2>/dev/null | "$BB" grep -q '^wpa_state=COMPLETED$' && break
    sleep 1
    n=$((n+1))
done
[ "$n" -lt 25 ] || fail AUTH
if [ "$MODE" = dhcp ]; then
    "$BB" udhcpc -f -n -i wlan0 -t 6 -T 2 -p "$RUN/udhcpc.pid" \
        -s /opt/cam/wlan/dhcp.sh > "$RUN/dhcp.log" 2>&1 </dev/null &
    n=0
    while [ "$n" -lt 20 ]; do
        [ -s "$RUN/ip" ] && break
        sleep 1
        n=$((n+1))
    done
    [ -s "$RUN/ip" ] || fail DHCP
else
    IP=$("$TOOL" --get "$RUN/candidate.conf" address) || fail CONFIG
    MASK=$("$TOOL" --get "$RUN/candidate.conf" netmask) || fail CONFIG
    GW=$("$TOOL" --get "$RUN/candidate.conf" gateway) || fail CONFIG
    "$BB" ifconfig wlan0 "$IP" netmask "$MASK" up || fail ADDRESS
    "$BB" route del default dev wlan0 2>/dev/null
    if [ -n "$GW" ]; then "$BB" route add default gw "$GW" dev wlan0 || fail ADDRESS; fi
    printf '%s\n' "$IP" > "$RUN/ip"
fi
read -r IP < "$RUN/ip"
"$TOOL" --valid-ip "$IP" || fail ADDRESS
"$BB" ifconfig wlan0 | "$BB" grep -q "inet addr:$IP " || fail ADDRESS
"$TOOL" --normalize "$RUN/candidate.conf" "$RUN/active.conf" || fail CONFIG
exit 0
