import pigpio
import smbus2
import time
import logging
from enum import Enum
from .rds import RDS

class Si4731:

    class HW(Enum):
        I2C_ADDRESS=0x63 # 0x63 (/SEN=1) or 0x11 (/SEN=0)
        RST_GPIO = 26
        SEN_GPIO = 16
        RECLK_GPIO = 4
        REFCLK_FREQ = 32768

    class CMDSET(Enum):
        POWER_UP=0x01
        GET_REV=0x10
        POWER_DOWN=0x11
        SET_PROPERTY=0x12
        GET_PROPERTY=0x13
        FM_TUNE_FREQ=0x20
        FM_TUNE_STATUS=0x22
        GET_INT_STATUS=0x14
        GET_RDS_STATUS=0x24

    class PROPS(Enum):
        REFCLK_FREQ = 0x0201
        REFCLK_PRESCALE = 0x0202
        DIGITAL_OUTPUT_SAMPLE_RATE = 0x0104
        DIGITAL_OUTPUT_FORMAT = 0x0102
        RX_VOLUME = 0x4000
        FM_RDS_INT_SOURCE = 0x1500
        FM_RDS_INT_FIFO_COUNT = 0x1501
        FM_RDS_CONFIG = 0x1502

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
        RDSINT = 0x04

    class FM_RDS_FLAGS(Enum):
        RDSRECV = 0x0001
        NOERRORS = 0xAA01


    def __init__(self):
        self.create_logger()
        self.init_hw()
        self.init_radio()
        self.rds = RDS()

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

        # Wait to ensure reset of device
        time.sleep(0.1)

        # Initialize i2c communication
        self.i2c = smbus2.SMBus(1)
        self.logger.debug("I2C bus open")

    def write_cmd(self, cmd, args):
        # Wait Clear To Send flag
        self.wait_cts()
        # Write command and arguments to i2c bus
        self.i2c.write_i2c_block_data(self.HW.I2C_ADDRESS.value, cmd.value, args)
        #self.logger.debug("Command sent: " + cmd.name + ", arguments: " + str(args))

    def read_cmd(self, cmd, nbytes):
        # Wait Clear To Send flag
        self.wait_cts()
        # Write command and read data from i2c bus
        return self.i2c.read_i2c_block_data(self.HW.I2C_ADDRESS.value, cmd.value, nbytes)

    def write_read_cmd(self, cmd, write, nread):
        # Write command and ACK INT
        wr=[cmd.value]
        wr.extend(write)
        write = smbus2.i2c_msg.write(self.HW.I2C_ADDRESS.value, wr)
        # Read status
        read = smbus2.i2c_msg.read(self.HW.I2C_ADDRESS.value, nread)
        # Execute I2C operation
        self.i2c.i2c_rdwr(write, read)
        # Convert response to list
        return list(read)


    def get_status(self):
        return self.i2c.read_byte(self.HW.I2C_ADDRESS.value)

    def wait_cts(self):
        while not self.get_status() & self.FLAGS.CTS.value:
            time.sleep(0.001)

    def get_int_status(self, intFlag):
        self.write_cmd(self.CMDSET.GET_INT_STATUS, [])
        if self.get_status() & intFlag.value:
            return True
        else:
            return False

    def wait_int(self, interruptType):
        #self.logger.debug("Waiting for " + interruptType.name + " interrupt...")
        while not self.get_int_status(interruptType):
            time.sleep(0.001)

    def power_up(self, outmode):
        # Create POWER_UP command
        cmd = self.CMDSET.POWER_UP
        args = [0x00]
        args.extend(outmode.value.to_bytes(1, byteorder='big'))
        # Send command
        self.write_cmd(cmd, args)
        self.logger.debug("Command sent: " + cmd.name + " with OUTMODE: " + outmode.name + " | " + str(args))

    def get_revision(self):
        # Send command
        resp=self.read_cmd(self.CMDSET.GET_REV, 9)
        partnumber = 'Si47' + str(resp[1])
        firmware = chr(resp[2]) + '.' + chr(resp[3])
        compfirmware = chr(resp[6]) + '.' + chr(resp[7])
        chiprev = chr(resp[8])
        self.logger.debug('Part Number: ' + partnumber)
        self.logger.debug('Firmware Revision: ' + firmware)
        self.logger.debug('Component Firmware Revision: ' + compfirmware)
        self.logger.debug('Chip Revision: ' + chiprev)

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
        # Get silicon revision
        self.get_revision()
        # REFCLK_FREQ
        self.write_property(self.PROPS.REFCLK_FREQ, self.HW.REFCLK_FREQ.value)
        # REFCLK_PRESCALE
        self.write_property(self.PROPS.REFCLK_PRESCALE, 1)
        # I2S output mode
        self.write_property(self.PROPS.DIGITAL_OUTPUT_FORMAT, self.OUTMODE.BITWIDTH24.value)
        # Sample rate 48000
        self.write_property(self.PROPS.DIGITAL_OUTPUT_SAMPLE_RATE, 48000)
        # Configure RDS interrupt source
        self.write_property(self.PROPS.FM_RDS_INT_SOURCE, self.FM_RDS_FLAGS.RDSRECV.value)
        # Set minimum RDS data for interrupt
        self.write_property(self.PROPS.FM_RDS_INT_FIFO_COUNT, 4)
        # Set accepted RDS data
        self.write_property(self.PROPS.FM_RDS_CONFIG, self.FM_RDS_FLAGS.NOERRORS.value)

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
        # Wait TUNE DONE interrupt
        self.wait_int(self.FLAGS.INTACK)
        self.logger.debug("Tuning done!")
        # ACK Interrupt and read status
        self.get_tune_status()

    def get_tune_status(self):
        # Send FM_TUNE_STATUS command, ACK INT, and read 8 bytes
        resp=self.write_read_cmd(self.CMDSET.FM_TUNE_STATUS, [self.FLAGS.INTACK.value], 8)

        # Process response
        validfreq = str(resp[1])
        freq = str(resp[2]*256 + resp[3])
        rssi = str(resp[4])
        snr = str(resp[5])
        tuncap = str(resp[7])
        self.logger.debug('Valid freq.: ' + validfreq)
        self.logger.debug('Fequency: ' + freq)
        self.logger.debug('RSSI: ' + rssi)
        self.logger.debug('SNR: ' + snr)
        self.logger.debug('Antenna tuning capacitor: ' + tuncap)

    def wait_rds(self):
        self.wait_int(self.FLAGS.RDSINT)
        #self.logger.debug("RDS data available.")


    def get_rds_status(self):
        # Send GET_RDS_STATUS command, ACK INT, and read 8 bytes
        resp=self.write_read_cmd(self.CMDSET.GET_RDS_STATUS, [self.FLAGS.INTACK.value], 13)
        blocka=resp[4]*256 + resp[5]
        blockb=resp[6]*256 + resp[7]
        blockc=resp[8]*256 + resp[9]
        blockd=resp[10]*256 + resp[11]
        gtype=self.rds.process_rds_blocks(blocka, blockb, blockc, blockd)
        if(gtype == RDS.GTYPES.STATION_NAME.value):
            self.logger.debug("Station Name: " + self.rds.PS.string)
        if(gtype == RDS.GTYPES.RADIO_TEXT.value):
            self.logger.debug("Radio Text: " + self.rds.RadioTextA.string)




