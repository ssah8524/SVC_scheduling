## For server side
cd SVC_scheduling
git pull
git clone https://github.com/oblique/create_ap.git
cd create_ap
make install

apt-get update
apt-get -y install isc-dhcp-client hostapd dnsmasq
modprobe ath5k
ifconfig wlan0 up
create_ap -n wlan0 node1-1 demo_main
