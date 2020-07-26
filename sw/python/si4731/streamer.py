import pyaudio
import time
from .mute_alsa import mute_alsa

def streamer_main(conn):
    # Change error handler for ALSA
    mute_alsa()

    # Init PyAudio
    pyAud = pyaudio.PyAudio()

    def callback(in_data, frame_count, time_info, status):
        return (in_data, pyaudio.paContinue)

    stream = pyAud.open(format=pyAud.get_format_from_width(4),
                        channels=2,
                        rate=48000,
                        input=True,
                        output=True,
                        stream_callback=callback,
                        output_device_index=2)

    stream.start_stream()
    conn.send('init_ok')

    run_app=True
    while(run_app):
        time.sleep(0.1)
        msg = conn.recv()
        if msg == 'quit':
            run_app=False

    stream.stop_stream()
    stream.close()

    pyAud.terminate()

