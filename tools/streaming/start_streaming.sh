#!/bin/sh
# Allwinner V316 Cam Live Streaming & WLAN Client Startup Script

# 1. Close inherited file descriptors from sdvcam to prevent video locks
for fd in $(ls /proc/$$/fd/ 2>/dev/null); do
    [ "$fd" -gt 2 ] 2>/dev/null && eval "exec $fd>&-" 2>/dev/null
done

# Wait for camera mode switch to complete
still_selected() {
    [ "$V316CM_MANAGED_STREAM" != 1 ] || [ -f /tmp/v316cm-stream-mode ]
}
sleep 2
still_selected || exit 0

# Read configuration from SD card
if [ -f /mnt/extsd/wlan.conf ]; then
    . /mnt/extsd/wlan.conf
fi

# Re-entering STREAM while connected must not interrupt the web controls.
if [ -n "$CAM_IP" ] && ifconfig wlan0 | grep -q "inet addr:$CAM_IP " &&
   pidof wpa_supplicant >/dev/null && netstat -ltn 2>/dev/null | grep -q ":$STREAM_PORT "; then
    echo "WLAN and HTTP already running - keeping current connection" >> /tmp/streaming.log
    touch /tmp/v316cm-stream-ready
    exit 0
fi
still_selected || exit 0

echo "=== STARTING WLAN CLIENT CONNECTION TO $ROUTER_SSID ===" > /tmp/streaming.log

# 2. Ensure WLAN kernel modules are loaded
if ! lsmod | grep -q xradio_wlan; then
    insmod /lib/modules/4.9.118/xradio_mac.ko 2>/dev/null
    insmod /lib/modules/4.9.118/xradio_core.ko 2>/dev/null
    insmod /lib/modules/4.9.118/xradio_wlan.ko 2>/dev/null
    sleep 1
fi

# 3. Stop old network daemons
killall wpa_supplicant hostapd udhcpd 2>/dev/null
ifconfig wlan0 down 2>/dev/null
sleep 0.5
still_selected || exit 0
ifconfig wlan0 up 2>/dev/null

# 4. Generate WPA configuration
mkdir -p /var/run/wpa_supplicant
cat << EOF_WPA > /tmp/wpa.conf
ctrl_interface=/var/run/wpa_supplicant
update_config=1
network={
    ssid="$ROUTER_SSID"
    psk="$ROUTER_PASS"
    key_mgmt=WPA-PSK
}
EOF_WPA

# 5. Start wpa_supplicant client
LD_LIBRARY_PATH=/mnt/extsd/lib:$LD_LIBRARY_PATH /mnt/extsd/bin/wpa_supplicant -B -i wlan0 -c /tmp/wpa.conf >> /tmp/streaming.log 2>&1
sleep 3
still_selected || exit 0

# 6. Configure IP address for Heimnetz
ifconfig wlan0 $CAM_IP netmask $NETMASK up
route add default gw $GATEWAY 2>/dev/null
echo "IP configured: $CAM_IP" >> /tmp/streaming.log

# 7. Start Telnet daemon for full remote shell over WiFi
killall telnetd 2>/dev/null
/mnt/extsd/bin/busybox telnetd -p 23 -l /bin/sh &
echo "Telnet server gestartet auf Port 23" >> /tmp/streaming.log

# 8. Start HTTP Streaming Server
chmod 755 /mnt/extsd/bin/busybox /mnt/extsd/bin/wpa_supplicant /mnt/extsd/www/cgi-bin/* 2>/dev/null
killall httpd 2>/dev/null
/mnt/extsd/bin/busybox httpd -p $STREAM_PORT -h /mnt/extsd/www
touch /tmp/v316cm-stream-ready

echo "=== STREAM READY AT http://$CAM_IP:$STREAM_PORT ===" >> /tmp/streaming.log
