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
