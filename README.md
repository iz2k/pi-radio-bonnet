# pi-radio-SI4731
Si473x i2c/i2s AM/FM radio receiver for Rasperrby Pi

## Hardware

A custom Pi Radio Bonnet is included in this project. The PCB features the SI4731-D60-GM IC, an AM/FM Broadcast Radio Receiver with RDS/RBDS. The reference clock is provided from the Pi through a hardware clock capable GPIO, and the I2C interface is used to control the functionality. i2s

Besides the radio receiver, the PCB also features two units of the MAX98357A 3W PCM Amplifier, providing high quality stereo output.

The I2S audio interface is used for all devices, where the Pi acts as the master device reading digital audio from the radio receiver through the I2S_DIN line, and providing digital audio data to the amplifiers through the I2S_DOUT line. 

## Raspberry Pi setup

In order to use the Pi Radio Bonnet, the following configurations have to be done in the Raspberry Pi OS:

### Enable I2S

``` bash
sudo nano /boot/config.txt
 -> dtparam=i2s=on # uncomment 
sudo reboot
```

### Compile and install I2S input device driver

For simplicity, the already existing driver for the I2S microphone ICS43432 from Invensense has been used. In order to compile it, you will need to install the kernel-headers first:

``` bash
sudo apt-get install raspberrypi-kernel-headers
```
Then just download the driver source and compile ir:
``` bash
mkdir ics43432
cd ics43432
wget https://raw.githubusercontent.com/raspberrypi/linux/rpi-$(uname -r | cut -d'.' -f1,2).y/sound/soc/codecs/ics43432.c
echo 'obj-m := 'ics43432'.o' > Makefile
make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
```
Finally install it on the system:
``` bash
sudo insmod ics43432.ko
```
If you get an error message about undefined symbols on the module, you may have missed rebooting the system after enabling I2S on the Pi. Just reboot and try to install it again.

You can test if the module was installed correctly executing the following command:
``` bash
lsmod | grep ics43432
```
You should see some modules with the ics43432 name on it loaded.

### Create dual I2S soundcard overlay

Now you need to create a soundcard overlay pointing to the i2s audio drivers. create the overlay configuration file:
``` bash
nano i2s-soundcard-overlay.dts
```
And paste the following into it:
```
/dts-v1/;
/plugin/;
/ {
   compatible = "brcm,bcm2708";
   fragment@0 {
       target = <&i2s>;
       __overlay__ {
           status = "okay";
       };
   };
   fragment@1 {
       target-path = "/";
       __overlay__ {
           codec_mic: card-codec {
               #sound-dai-cells = <0>;
               compatible = "invensense,ics43432";
               status = "okay";
           };
           codec_amp: pcm5102a-codec {
               #sound-dai-cells = <0>;
               compatible = "ti,pcm5102a";
               status = "okay";
           };
       };
   };
   fragment@2 {
       target = <&sound>;
       master_overlay: __dormant__ {
           compatible = "simple-audio-card";
           simple-audio-card,format = "i2s";
           simple-audio-card,name = "soundcard";
           simple-audio-card,bitclock-master = <&dailink0_master>;
           simple-audio-card,frame-master = <&dailink0_master>;
           status = "okay";
           simple-audio-card,cpu {
               sound-dai = <&i2s>;
           };
           dailink0_master: simple-audio-card,codec {
               sound-dai = <&codec_mic>;
           };
       };
   };
   fragment@3 {
       target = <&sound>;
       slave_overlay: __overlay__ {
               compatible = "simple-audio-card";
               simple-audio-card,format = "i2s";
               simple-audio-card,name = "soundcard";
               status = "okay";
               simple-audio-card,dai-link@0 {
                   reg = <0>;
                   format = "i2s";
                   cpu {
                       sound-dai = <&i2s>;
                   };
                   codec {
                       sound-dai = <&codec_mic>;
                   };
               };
               simple-audio-card,dai-link@1 {
                   reg = <1>;
                   format = "i2s";
                   cpu {
                       sound-dai = <&i2s>;
                   };
                   codec {
                       sound-dai = <&codec_amp>;
                   };
               };
       };
   };
   __overrides__ {
       alsaname = <&master_overlay>,"simple-audio-card,name",
                   <&slave_overlay>,"simple-audio-card,name";
       master = <0>,"=2!3";
   };
};
```

Now compile the overlay itself and copy it to the system. Don't care about the warnings during compilation.
``` bash
dtc -@ -I dts -O dtb -o i2s-soundcard.dtbo i2s-soundcard-overlay.dts
sudo cp i2s-soundcard.dtbo /boot/overlays
```

Finally, enable the new overlay in the boot configuration:
``` bash
sudo nano /boot/config.txt
 -> dtparam=i2s=on      # keep uncommented
 -> #dtparam=audio=on   # comment
 -> dtdebug=1           # add for debugging at boot dmesg
 -> dtoverlay=i2s-soundcard,alsaname=sndrpisimplecar # add
sudo reboot
```

You should now already see the new playback and capture devies by running:
``` bash
aplay -l
**** List of PLAYBACK Hardware Devices ****
card 0: sndrpisimplecar [sndrpisimplecar], device 0: bcm2835-i2s-pcm5102a-hifi pcm5102a-hifi-0 [bcm2835-i2s-pcm5102a-hifi pcm5102a-hifi-0]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
```
``` bash
arecord -l
**** List of CAPTURE Hardware Devices ****
card 0: sndrpisimplecar [sndrpisimplecar], device 1: bcm2835-i2s-ics43432-hifi ics43432-hifi-1 [bcm2835-i2s-ics43432-hifi ics43432-hifi-1]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
```

### Add ALSA configuration

In order to improve the integration of the new soundcard in the OS let's add an ALSA configuration file.
``` bash
sudo nano /etc/asound.conf
```

And paste the following into it:
```
pcm.!default {
   type asym
   capture.pcm "sharedmic_sv"
   playback.pcm "speaker_sv"
}
pcm.sharedmic_sv {
   type softvol
   slave.pcm "sharedmic"
   control {
	name "Boost Capture Volume"
	card sndrpisimplecar
   }
   min_dB -2.0
   max_dB 20.0
}
pcm.sharedmic {
   type plug
   slave.pcm "dsnooped"
}
pcm.dsnooped {
   type dsnoop
   ipc_key 777777
   ipc_perm 0677
   slave {
       pcm "hw:0,1"
       channels 2
       format S32_LE
   }
}
pcm.speaker_sv {
   type softvol
   slave.pcm "speaker"
   control.name "Speaker Volume"
   control.card 0
}
pcm.speaker{
   type plug
   slave.pcm "dmixed"
}
pcm.dmixed {
  type dmix
  ipc_key 888888
  ipc_perm 0677
  #ipc_key_add_uid false
  slave {
    pcm "hw:0,0"
    period_time 0
    period_size 1024
    buffer_size 8192
    rate 44100
    channels 2
  }
  bindings {
       0 0
       1 1
  }
}

```
With this configuration software volume control is added to both, capture and playback devices, and a channel mixer is added to the playback hardware to support simultaneous playback of multiple sources.

Finally, reboot again:
``` bash
sudo reboot
```

And just in case, test if the speakers are working fine:
``` bash
speaker-test -c2 -twav -l7
```

Prior to testing the radio receiver, the device has to be initiated by software.

## Control software

In order to initialize the radio receiver, the REFCLK clock has to be enabled and a reset pulse has to be sent. Next, the I2C bus can be used to send commands to the device, set volume, band, frequency and alike.

A python programm is included in the project to do all of this for you. Before running the programm, some dependencies have to be installed.

### PIGPIO

The control of the GPIOs for REFCLK and RST and SEN signals is done by means of the pigpio deamon. This is a low level GPIO controller that can be commanded through other programms like the python program used in this project.

Install the deamon running the following commands:
``` bash
sudo apt-get install pigpio
```
Next, modify the systemd init script to specify pigpiod to work with PWM clock peripheral. By default it works with PCM, which we want to use for I2S instead.

Edit the following file and replace -l with -t 0 in the ExecStart line.
``` bash
sudo nano /lib/systemd/system/pigpiod.service
```

Now, enable autostart for pigpiod:
``` bash
sudo systemctl enable pigpiod.service
sudo systemctl start pigpiod.service
```

Finally, install the python3 package to control the pigpio deamon from the program.

``` bash
sudo apt-get install python3-pigpio
```

### SMBUS

The python program uses the SMBUS package for the I2C communication. Install it as follows:

``` bash
sudo apt-get install python3-smbus
```

## Usage

In order to tune the radio receiver, execute the python program. You may want to modify main.py in order to set a different frequency.

``` bash
python3 sw/python/main.py
```

Try recording from the capture device (stop the reccording with CTRL+C):
``` bash
arecord -D default -c2 -r 48000 -f S32_LE -t wav -V steres -v test.wav
```

Play the recorded audio file:
``` bash
aplay test.wav
```

If everything went well, you should hear the recorded radio dial.

Now, you can also try piping directly the audio from the radio receiver to the speakers:
``` bash
 arecord -c2 -r 48000 -f S32_LE -t wav -V stereo | sudo aplay
```
Some improvements are still missing to avoid using sudo and keeping the system alive after closing the pipe.

You can also control the volume of the soundcard with alsamixer:
``` bash
alsamixer
```

And store the new values as default if desired:
``` bash
sudo alsactl store
```
