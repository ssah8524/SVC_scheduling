cd SVC_scheduling
git pull
apt-get update
apt-get -y install isc-dhcp-client
modprobe ath5k
ifconfig wlan0 up
wpa_passphrase node1-1 demo_main > wpa.conf
wpa_supplicant -iwlan0 -cwpa.conf -B
dhclient wlan0
