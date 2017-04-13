
#cd SVC_scheduling
#git pull
apt-get update
apt-get -y install isc-dhcp-client
modprobe ath5k
#modprobe ath9k
ifconfig wlan0 up
wpa_passphrase node1-1 demo_main > wpa.conf
wpa_supplicant -iwlan0 -cwpa.conf -B
dhclient wlan0


## For server side
git clone https://github.com/oblique/create_ap.git
cd create_ap
make install

apt-get update
apt-get -y install isc-dhcp-client hostapd dnsmasq
modprobe ath5k
ifconfig wlan0 up
create_ap -n wlan0 node1-1 demo_main
