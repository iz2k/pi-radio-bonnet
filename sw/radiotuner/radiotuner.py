#!/usr/bin/env python3
from backend.streamer import AudioPipe
from backend.player import player_main
from frontend.tui import TUI_main
from frontend.webserver import define_webserver
from threading import Thread
from queue import Queue
import argparse
import socket

# Parse arguments
parser = argparse.ArgumentParser(description='Tune FM radio.')
parser.add_argument(metavar='freq', type=float, dest='freq',
                    help='the tune frequency in MHz')

parser.add_argument("-ui", default='none', help=" select User Interface none/terminal/web")
parser.add_argument("-port", default='8081', help=" port used for web UI")

args = parser.parse_args()

if args.ui != 'none' and args.ui != 'terminal' and args.ui != 'web':
    print('Invalid UI. Please use: none | terminal | web')
    quit()

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
#audio = AudioPipe()

try:
    # Start streaming audio from Radio to Speaker
    #audio.start()

    # Start player thread
    th_player.start()

    if args.ui =='terminal':
        th_tui.start()

    # This has to go last, as sio.run is blocking
    if args.ui == 'web':
        print('Starting Web UI on: http://' + str(socket.gethostname()) + ':' + str(args.port))
        # Start Webserver
        sio.run(app, port=args.port, host='0.0.0.0', debug=False)
        # When server ends, end app
        player_q.put(['quit',0])

    # Wait for threads to end
    if th_tui.is_alive():
        th_tui.join()

    if th_player.is_alive():
        th_player.join()

    # Stop audio stream
    #if audio is not None:
    #    audio.stop()

except KeyboardInterrupt:
    if th_tui.is_alive():
        tui_q.put(['quit', None, None])
        th_tui.join()

    if th_player.is_alive():
        player_q.put(['quit',0])
        th_player.join()

    #if audio is not None:
    #    audio.stop()
