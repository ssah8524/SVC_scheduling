apt-get update  
apt-get -y install git

# Get experiment source code
git clone -b demo https://github.com/ssah8524/SVC_scheduling.git  

# Get tools needed by the AP
git clone https://github.com/oblique/create_ap.git

cd ~/create_ap
make install

apt-get -y install hostapd dnsmasq python-numpy

# Get tools used by client to decode video
apt-get -y install libav-tools libx264-dev yasm pkg-config

cd ~
git clone -b demo https://github.com/ffund/SVC-Layer-multiplexing-demultiplexing.git multiplex

cd ~/multiplex/SVC_layer_multiplexer/
make

cd ~/multiplex/H264Extension/build/linux/
make decoder

cd ~
wget http://ffmpeg.org/releases/ffmpeg-3.3.tar.bz2
tar -vxjf ffmpeg-3.3.tar.bz2 
cd ffmpeg-3.3
./configure --enable-libx264 --enable-gpl 
make
make install
