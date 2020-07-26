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
echo " -> Installing Python AlsaAudio library"
sudo apt-get -y install python3-alsaaudio

echo ""
echo "***************************"
echo "* System install finished *"
echo "***************************"
echo " -> Please, reboot: sudo reboot"
