import si4731_h
import pigpio
import smbus
import time
import logging


class Si4731:
    # REFCLK feed configuration
    REFCLK_FREQ = 34406
    RECLK_GPIO = 4

    # i2c bus controller
    i2c = None

    def __init__(self):
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
        # Set HW clock to feed REFCLK
        pi = pigpio.pi()
        pi.hardware_clock(self.RECLK_GPIO, self.REFCLK_FREQ)
        self.logger.debug("REFCLK enabled")
        self.i2c = smbus.SMBus(1)
        self.logger.debug("I2C bus open")

    def byteHigh(self, val):
        return val >> 8

    def byteLow(self, val):
        return val & 0xFF

    def wait_cts(self):
        status = 0
        self.logger.debug("Waiting CTS")
        while not status & si4731_h.STATUS_CTS:
            status = self.i2c.read_byte(si4731_h.I2C_ADDRESS)
        self.logger.debug("CTS received!")

    def wait_int(self, interruptType):
        status = 0
        self.logger.debug("Waiting interrupt: " + str(hex(interruptType)))
        while not status & interruptType:
            self.write_cmd(si4731_h.CMD_GET_INT_STATUS, [])
            time.sleep(0.125)
            status = self.i2c.read_byte(si4731_h.I2C_ADDRESS)
        self.logger.debug("Interrupt received!")

    def write_cmd(self, cmd, *args):
        self.wait_cts()
        self.i2c.write_i2c_block_data(si4731_h.I2C_ADDRESS, cmd, *args)
        self.logger.debug("Writing command:" + str(hex(cmd)) + " with args " + str(args))

    def write_property(self, prop, val):
        self.wait_cts()
        self.i2c.write_i2c_block_data(si4731_h.I2C_ADDRESS, 0x12, [0x00, self.byteHigh(prop), self.byteLow(prop), self.byteHigh(val), self.byteLow(val)])

    def init(self):
        # POWER ON
        self.write_cmd(si4731_h.CMD_POWER_UP, [0x00, si4731_h.OUT_BOTH])
        # REFCLK_FREQ
        self.write_property(si4731_h.PROP_REFCLK_FREQ, self.REFCLK_FREQ)
        # REFCLK_PRESCALE
        self.write_property(si4731_h.PROP_REFCLK_PRESCALE, 1)
        # I2S output mode
        self.write_property(si4731_h.PROP_DIGITAL_OUTPUT_FORMAT, si4731_h.OUT_24BIT)
        # Sample rate 48000
        self.write_property(si4731_h.PROP_DIGITAL_OUTPUT_SAMPLE_RATE, 48000)

    def set_volume(self, vol):
        # Volume value goes from 0 to 63
        if 0 <= vol <= 63:
            self.write_property(si4731_h.PROP_RX_VOLUME, vol)
            self.logger.debug("Setting volume to " + str(vol) + " ("+str(int(vol*100/63))+"%)")
        else:
            self.logger.warning("Volume out of range. Please set a value between 0 and 63")

    def tune(self, freq_MHz):
        # FM_TUNE_FREQ
        self.write_cmd(si4731_h.CMD_FM_TUNE_FREQ, [0x00, self.byteHigh(int(freq_MHz*100)), self.byteLow(int(freq_MHz*100)), 0x00, 0x00])
        self.wait_int(si4731_h.FLG_INTACK)
        # ACK INT TUNED
        self.write_cmd(si4731_h.CMD_FM_TUNE_STATUS, [si4731_h.FLG_INTACK])