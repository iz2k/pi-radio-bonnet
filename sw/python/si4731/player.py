import alsaaudio
from .si4731 import Si4731

def player_main(player_q, tui_q):
    mixer = alsaaudio.Mixer('Speaker')
    volume = mixer.getvolume()[0]

    radio=Si4731()
    radio.set_volume(40)    # Radio at 100% of volume
    radio.fm_tune(97.2)     # Initial station
    radio.get_rsq_status()

    run_app=True
    while(run_app):
        # Update Radio Signal Quality
        radio.get_rsq_status()

        # Check if RDS data vailable
        if (radio.check_rds()):
            # Get and Process RDS data
            radio.get_rds_status()

        # Check if msg in queue
        while player_q.empty() is False:
            player_q_msg = player_q.get()
            if (player_q_msg is 'seek_up'):
                radio.fm_seek_up()
            if (player_q_msg is 'seek_down'):
                radio.fm_seek_down()
            if (player_q_msg is 'vol_up'):
                if (volume<95):
                    volume=volume+5
                else:
                    volume=100
                mixer.setvolume(volume)
                radio.set_volume(int(volume*0.63))
            if (player_q_msg is 'vol_down'):
                if (volume > 5):
                    volume = volume - 5
                else:
                    volume = 0
                mixer.setvolume(volume)
                radio.set_volume(int(volume*0.63))
            if (player_q_msg is 'quit'):
                run_app=False

        # Update TUI
        tui_q.put([radio, volume])
