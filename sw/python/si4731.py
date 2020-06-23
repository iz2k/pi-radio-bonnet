import pigpio
import smbus
import time
import logging
from enum import Enum

class Si4731:

    class HW(Enum):
        I2C_ADDRESS=0x63 # 0x63 (/SEN=1) or 0x11 (/SEN=0)
        RST_GPIO = 26
        SEN_GPIO = 16
        RECLK_GPIO = 4
        REFCLK_FREQ = 34406

    class CMDSET(Enum):
        POWER_UP=0x01
        GET_REV=0x10
        POWER_DOWN=0x11
        SET_PROPERTY=0x12
        GET_PROPERTY=0x13
        FM_TUNE_FREQ=0x20
        FM_TUNE_STATUS=0x22
        GET_INT_STATUS=0x14

    class PROPS(Enum):
        REFCLK_FREQ = 0x0201
        REFCLK_PRESCALE = 0x0202
        DIGITAL_OUTPUT_SAMPLE_RATE = 0x0104
        DIGITAL_OUTPUT_FORMAT = 0x0102
        RX_VOLUME = 0x4000

    class RFMODE(Enum):
        LW = 0
        AM = 1
        SW = 2
        FM = 3

    class OUTMODE(Enum):
        RDS=0x00  # RDS only
        ANALOG=0x05
        DIGITAL1=0x0B # DCLK, LOUT/DFS, ROUT/DIO
        DIGITAL2=0xB0 # DCLK, DFS, DIO
        BOTH=(ANALOG | DIGITAL2)
        BITWIDTH24 = 0x0002

    class FLAGS(Enum):
        CTS = 0x80
        ERR = 0x40
        STCINT = 0x01
        INTACK = 0x01

    def __init__(self):
        self.create_logger()
        self.init_hw()
        self.init_radio()

    def create_logger(self):
        # create logger
        self.logger = logging.getLogger('Si4731')
        self.logger.setLevel(logging.DEBUG)
        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # create formatter
        formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s]: %(message)s')
        # add formatter to ch
        ch.setFormatter(formatter)
        # add ch to logger
        self.logger.addHandler(ch)

    def init_hw(self):
        # Set HW clock to feed REFCLK
        self.pi = pigpio.pi()

        # Reset the device
        self.pi.set_mode(self.HW.RST_GPIO.value, pigpio.OUTPUT)
        self.pi.set_mode(self.HW.SEN_GPIO.value, pigpio.OUTPUT)
        self.pi.write(self.HW.RST_GPIO.value, 0)
        self.pi.write(self.HW.SEN_GPIO.value, 1)
        self.logger.debug("RST adn SEN GPIOs initialized.")

        self.pi.hardware_clock(self.HW.RECLK_GPIO.value, self.HW.REFCLK_FREQ.value)
        self.logger.debug("REFCLK enabled @" + str(self.HW.REFCLK_FREQ.value) + 'Hz')

        # Wait to ensure reset of device
        time.sleep(0.1)
        # Set /RST high
        self.pi.write(self.HW.RST_GPIO.value, 1)
        self.logger.debug("Device Reset!")

        # Initialize i2c communication
        self.i2c = smbus.SMBus(1)
        self.logger.debug("I2C bus open")

    def write_cmd(self, cmd, args):
        # Wait Clear To Send flag
        self.wait_cts()
        # Write command and arguments to i2c bus
        self.i2c.write_i2c_block_data(self.HW.I2C_ADDRESS.value, cmd.value, args)
        #self.logger.debug("Command sent: " + cmd.name + ", arguments: " + str(args))

    def wait_cts(self):
        status = 0
        #self.logger.debug("Waiting for CTS...")
        while not status & self.FLAGS.CTS.value:
            status = self.i2c.read_byte(self.HW.I2C_ADDRESS.value)

    def wait_int(self, interruptType):
        status = 0
        self.logger.debug("Waiting for " + interruptType.name + " interrupt...")
        while not status & interruptType.value:
            self.write_cmd(self.CMDSET.GET_INT_STATUS, [])
            time.sleep(0.1)
            status = self.i2c.read_byte(self.HW.I2C_ADDRESS.value)

    def power_up(self, outmode):
        # Create POWER_UP command
        cmd = self.CMDSET.POWER_UP
        args = [0x00]
        args.extend(outmode.value.to_bytes(1, byteorder='big'))
        # Send command
        self.write_cmd(cmd, args)
        self.logger.debug("Command sent: " + cmd.name + " with OUTMODE: " + outmode.name + " | " + str(args))

    def write_property(self, prop, val):
        # Create SET_PROPERTY command
        cmd = self.CMDSET.SET_PROPERTY
        args = [0x00]
        args.extend(prop.value.to_bytes(2, byteorder='big'))
        args.extend(val.to_bytes(2, byteorder='big'))
        # Send command
        self.write_cmd(cmd, args)
        self.logger.debug("Command sent: " + cmd.name + " with PROPERTY: " + prop.name + " and VALUE: " + str(val) + " | " + str(args))

    def init_radio(self):
        # POWER ON
        self.power_up(self.OUTMODE.BOTH)
        # REFCLK_FREQ
        self.write_property(self.PROPS.REFCLK_FREQ, self.HW.REFCLK_FREQ.value)
        # REFCLK_PRESCALE
        self.write_property(self.PROPS.REFCLK_PRESCALE, 1)
        # I2S output mode
        self.write_property(self.PROPS.DIGITAL_OUTPUT_FORMAT, self.OUTMODE.BITWIDTH24.value)
        # Sample rate 48000
        self.write_property(self.PROPS.DIGITAL_OUTPUT_SAMPLE_RATE, 48000)

    def set_volume(self, vol):
        # Volume value goes from 0 to 63
        if 0 <= vol <= 63:
            self.logger.debug("Setting volume to " + str(vol) + " ("+str(int(vol*100/63))+"%)")
            self.write_property(self.PROPS.RX_VOLUME, vol)
        else:
            self.logger.warning("Volume out of range. Please set a value between 0 and 63")

    def fm_tune(self, freq_MHz):
        # Create FM_TUNE_FREQ command
        cmd = self.CMDSET.FM_TUNE_FREQ
        args = [0x00]
        args.extend(int((freq_MHz*100)).to_bytes(2, byteorder='big'))
        args.extend([0x00, 0x00])
        # Send command
        self.write_cmd(cmd, args)
        self.logger.debug("Command sent: " + cmd.name + " with FREQUENCY: " + str(freq_MHz) + " | " + str(args))
        # Wait ACK interrupt
        self.wait_int(self.FLAGS.INTACK)
        # ACK INT TUNED
        self.write_cmd(self.CMDSET.FM_TUNE_STATUS, [self.FLAGS.INTACK.value])
        self.logger.debug(self.FLAGS.INTACK.name + " acknowledged.")
