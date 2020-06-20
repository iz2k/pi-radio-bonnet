import SiRadio

radio = SiRadio.Si4731()
radio.init()
radio.set_volume(40)
radio.tune(100)