from si4731 import Si4731

radio=Si4731()
radio.set_volume(63)
radio.fm_tune(97.2)
while(1):
    radio.wait_rds()
    radio.get_rds_status()