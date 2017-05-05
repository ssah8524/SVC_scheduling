apt-get update  
apt-get -y install git

git clone -b demo https://github.com/ssah8524/SVC_scheduling.git  

git clone https://github.com/oblique/create_ap.git

cd ~/create_ap
make install

apt-get -y install hostapd dnsmasq python-numpy

apt-get -y install libav-tools

cd ~
git clone -b demo https://github.com/ffund/SVC-Layer-multiplexing-demultiplexing.git multiplex

cd ~/multiplex/SVC_layer_multiplexer/
make

cd ~/multiplex/H264Extension/build/linux/
make decoder

