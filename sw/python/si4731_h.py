#Si4731 i2c address 0x63 (/SEN=1) or 0x11 (/SEN=0)
I2C_ADDRESS=0x11

# Commands
CMD_POWER_UP=0x01
CMD_GET_REV=0x10
CMD_POWER_DOWN=0x11
CMD_SET_PROPERTY=0x12
CMD_GET_PROPERTY=0x13
CMD_FM_TUNE_FREQ=0x20
CMD_FM_TUNE_STATUS=0x22
CMD_GET_INT_STATUS=0x14

# Output modes
OUT_RDS=0x00  # RDS only
OUT_ANALOG=0x05
OUT_DIGITAL1=0x0B # DCLK, LOUT/DFS, ROUT/DIO
OUT_DIGITAL2=0xB0 # DCLK, DFS, DIO
OUT_BOTH=(OUT_ANALOG | OUT_DIGITAL2)
OUT_24BIT = 0x0002

# Statuses
STATUS_CTS = 0x80
STATUS_ERR = 0x40
STATUS_STCINT = 0x01

# Properties
PROP_REFCLK_FREQ = 0x0201
PROP_REFCLK_PRESCALE = 0x0202
PROP_DIGITAL_OUTPUT_SAMPLE_RATE = 0x0104
PROP_DIGITAL_OUTPUT_FORMAT = 0x0102
PROP_RX_VOLUME = 0x4000

# Flags
FLG_INTACK = 0x01

# Modes
MODE_LW = 0
MODE_AM = 1
MODE_SW = 2
MODE_FM = 3