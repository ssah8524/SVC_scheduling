## For server side
cd SVC_scheduling
git pull
git clone https://github.com/oblique/create_ap.git
cd create_ap
make install

apt-get update
apt-get -y install isc-dhcp-client hostapd dnsmasq
# Also install numpy library, needed for the scheduler
apt-get -y install python-numpy

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
create_ap -n -g 192.168.0.100 wlan0 svcdemo demo_main
