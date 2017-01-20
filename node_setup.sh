
#cd SVC_scheduling
#git pull
apt-get update
apt-get -y install isc-dhcp-client
modprobe ath5k
#modprobe ath9k
ifconfig wlan0 up
wpa_passphrase node1-1 simpletest > wpa.conf
wpa_supplicant -iwlan0 -cwpa.conf -B
dhclient wlan0
