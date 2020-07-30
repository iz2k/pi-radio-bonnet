import alsaaudio
import time
from si4731.si4731 import Si4731

def player_main(player_q, tui_q, sio, freq):
    mixer = alsaaudio.Mixer()
    volume = mixer.getvolume()[0]

    radio=Si4731()
    radio.fm_tune(freq)     # Initial station
    radio.get_rsq_status()

    ui_update_cnt = 0

    try:
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
                if (player_q_msg[0] == 'turn_on'):
                    radio.turn(True)
                if (player_q_msg[0] == 'turn_off'):
                    radio.turn(False)
                if (player_q_msg[0] == 'seek_up'):
                    radio.fm_seek_up()
                if (player_q_msg[0] == 'seek_down'):
                    radio.fm_seek_down()
                if (player_q_msg[0] == 'vol_up'):
                    if (volume<95):
                        volume=volume+5
                    else:
                        volume=100
                    mixer.setvolume(volume)
                if (player_q_msg[0] == 'vol_down'):
                    if (volume > 5):
                        volume = volume - 5
                    else:
                        volume = 0
                    mixer.setvolume(volume)
                if (player_q_msg[0] == 'vol'):
                    volume = player_q_msg[1]
                    if (volume > 100):
                        volume = 100
                    if (volume < 0):
                        volume = 0
                    mixer.setvolume(volume)
                if (player_q_msg[0] is 'quit'):
                    run_app=False

            # Update TUI
            ui_update_cnt = ui_update_cnt + 1
            if ui_update_cnt > 10:
                tui_q.put(['radiovol', radio, volume])
                sio.emit('radio', radio.get_info_obj())
                sio.emit('volume', volume)
                ui_update_cnt = 0
            time.sleep(0.01)
    except:
        pass
