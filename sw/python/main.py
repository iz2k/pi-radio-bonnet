#!/usr/bin/env python3
from si4731.streamer import AudioPipe
from si4731.player import player_main
from si4731.tui import TUI_main
from si4731.webserver import define_webserver, shutdown_server
from threading import Thread
from queue import Queue
import argparse

# Parse arguments
parser = argparse.ArgumentParser(description='Tune FM radio.')
parser.add_argument(metavar='freq', type=float, dest='freq',
                    help='the tune frequency in MHz')

parser.add_argument("-ui", default='none', help=" select User Interface none/terminal/web")

args = parser.parse_args()

# Create inter thread communication queues
player_q = Queue()
tui_q = Queue()

# Create WebServer (without starting it)
[app, sio] = define_webserver(player_q)

# Create player thread (without starting it)
th_player = Thread(target=player_main, args=(player_q, tui_q, sio, args.freq))

# Create TUI thread (without starting it)
th_tui = Thread(target=TUI_main, args=(tui_q, player_q))

# Create streamer (without starting it)
audio = AudioPipe()

try:
    # Start streaming audio from Radio to Speaker
    audio.start()

    # Start player thread
    th_player.start()

    if args.ui =='terminal':
        th_tui.start()

    # This has to go last, as sio.run is blocking
    if args.ui == 'web':
        # Start Webserver
        sio.run(app, port=8081, host='0.0.0.0', debug=False)
        # When server ends, end app
        player_q.put('quit')

    # Wait for threads to end
    if th_tui.is_alive():
        th_tui.join()

    if th_player.is_alive():
        th_player.join()

    # Stop audio stream
    if audio is not None:
        audio.stop()

except KeyboardInterrupt:
    if th_tui.is_alive():
        tui_q.put(['quit', None, None])
        th_tui.join()

    if th_player.is_alive():
        player_q.put('quit')
        th_player.join()

    if audio is not None:
        audio.stop()
