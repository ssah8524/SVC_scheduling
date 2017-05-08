# Bring up ath9k interface as wlan0 if there is one
# ath5k as second choice
athdriver=$(lspci | grep "Atheros")
if [[ $athdriver == *"AR9"* ]]; then
modprobe ath9k
sleep 1
fi

athdriver=$(lspci | grep "Atheros")
if [[ $athdriver == *"AR5"* ]]; then
modprobe ath5k
sleep 1
fi

ifconfig wlan0 up

# Kill wpa_supplicant if it's already running
# Otherwise, you will keep getting disconnected
# as the two processes compete
killall wpa_supplicant
wpa_passphrase svcdemo demo_main > wpa.conf
wpa_supplicant -iwlan0 -cwpa.conf -B

num=$(hostname -s | cut -f2 -d'-')
ifconfig wlan0 192.168.0.$num
