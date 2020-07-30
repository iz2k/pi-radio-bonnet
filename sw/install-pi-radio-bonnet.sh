#!/bin/bash

echo "This script will install audio drivers and"
echo "sw ependencies for PI-RADIO-BONNET project"
echo ""

echo ""
echo "***************************"
echo "* Enabling HW peripherals *"
echo "***************************"

echo " >> Enabling I2C"
sudo raspi-config nonint do_i2c 0


echo ""
echo " >> Enabling I2S"

# Remove undesired lines
sudo sed -i \
	-e "s/^dtparam=audio=on/#\0/" \
	-e "s/^#\(dtparam=i2s=on\)/\1/" \
	/boot/config.txt

# Add i2s-mmap if not present
grep -q "dtoverlay=i2s-mmap" /boot/config.txt || \
	echo "dtoverlay=i2s-mmap" | sudo tee -a /boot/config.txt

# Add i2s if not present
grep -q "dtparam=i2s=on" /boot/config.txt || \
	echo "dtparam=i2s=on" | sudo tee -a /boot/config.txt

echo ""
echo " >> Enabling googlevoicehat-soundcard"

# Add dtoverlay if not present
grep -q "dtoverlay=googlevoicehat-soundcard" /boot/config.txt || \
	echo "dtoverlay=googlevoicehat-soundcard" | sudo tee -a /boot/config.txt

echo ""
echo " >> Configuring mixer on ALSA"

cat <<EOF | sudo tee /etc/asound.conf
pcm.speaker {
	type softvol
	slave.pcm dmix
	control {
		name Master
		card 0
	}
}

pcm.mic {
	type route
	slave.pcm dsnoop
	ttable {
		0.0 1
		1.1 1
	}
}

pcm.!default {
	type asym
	playback.pcm "plug:speaker"
	capture.pcm "plug:mic"
}

ctl.!default {
	type hw
	card 0
}
EOF

echo "********************"
echo "* Updating sources *"
echo "********************"

sudo apt-get update

echo ""
echo "***************************"
echo "* Installing Dependencies *"
echo "***************************"

echo ""
echo " >> Installing PiGPIO"
sudo apt-get -y install pigpio

echo ""
echo " -> Configuring pigpiod service"

cat <<EOF | sudo tee /lib/systemd/system/pigpiod.service
[Unit]
Description=Daemon required to control GPIO pins via pigpio
[Service]
ExecStart=/usr/bin/pigpiod -t 0
ExecStop=/bin/systemctl kill pigpiod
Type=forking
[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable pigpiod.service
sudo systemctl start pigpiod.service

echo ""
echo " >> Installing Python Packet Manager"
sudo apt-get -y install python3-pip
echo ""
echo " -> Installing Python PiGPIO library"
sudo pip3 install pigpio

echo ""
echo " -> Installing Python SMBUS2 library"
sudo pip3 install smbus2

echo ""
echo " -> Installing Python Flask library"
sudo pip3 install flask

echo ""
echo " -> Installing Python eventlet library"
sudo pip3 install eventlet

echo ""
echo " -> Installing Python Flask library"
sudo pip3 install flask_socketio

echo ""
echo " -> Installing Python AlsaAudio library"
sudo apt-get -y install python3-alsaaudio

echo ""
echo "*********************************"
echo "* Installing Audio Pipe service *"
echo "*********************************"
echo ""
echo ""
echo " -> Creating Audio Pipe Service"
cat <<EOF | sudo tee /etc/systemd/system/audio-pipe.service
[Unit]
Description=Audio Pipe

[Service]
ExecStart=bash /usr/share/radiotuner/backend/stream.sh
WorkingDirectory=/usr/share/radiotuner
StandardOutput=inherit
StandardError=inherit
Restart=always
User=root
 
[Install]
WantedBy=multi-user.target
EOF

echo " -> Reloading systemctl service daemons."
sudo systemctl daemon-reload

echo " -> Enabling Audio Pipe service."
sudo systemctl enable audio-pipe.service
sudo systemctl start audio-pipe.service

echo ""
echo "******************************"
echo "* Installing Custom Software *"
echo "******************************"
echo ""
echo " -> Removing previous versions"
sudo rm -rf /usr/share/radiotuner

echo ""
echo " -> Downloading last version"
wget -O radiotuner.zip https://github.com/iz2k/pi-radio-bonnet/raw/master/sw/release/current/radiotuner.zip

echo ""
echo " -> Extracting files"
sudo unzip -o -d /usr/share radiotuner.zip

echo ""
echo " -> Making radiotuner executable"
sudo chmod +x /usr/share/radiotuner/radiotuner.py

echo ""
echo " -> Creating symbolic link in /usr/bin"
sudo ln -f -s /usr/share/radiotuner/radiotuner.py /usr/bin/radiotuner


echo ""
echo "***************************"
echo "* System install finished *"
echo "***************************"
echo " -> Please, reboot: sudo reboot"
