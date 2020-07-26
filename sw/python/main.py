from threading import Thread
from queue import Queue
from si4731.streamer import AudioPipe
from si4731.player import player_main
from si4731.tui import TUI_main
from si4731.webserver import server_main
import argparse
import socketio
import eventlet

parser = argparse.ArgumentParser(description='Tune FM radio.')
parser.add_argument(metavar='freq', type=float, dest='freq',
                    help='the tune frequency in MHz')

parser.add_argument("--ui", default='none', help=" select User Interface none/terminal/web")

args = parser.parse_args()

# Create inter thread communication queues
player_q = Queue()
tui_q = Queue()
web_q = Queue()

sio = socketio.Server(cors_allowed_origins='*')

# Create player thread
th_player = Thread(target=player_main, args=(player_q, tui_q, sio, args.freq))

# Create TUI thread
th_tui = Thread(target=TUI_main, args=(tui_q, player_q))

# Create WEB thread
th_web = Thread(target=server_main, args=(sio, web_q, player_q))

# Create streamer
audio = AudioPipe()


try:
    audio.start()
    th_player.start()
    th_web.start()

    if(args.ui == 'terminal'):
        th_tui.start()

    # Wait for threads to end
    if (args.ui == 'terminal'):
        th_tui.join()

    th_web.join()
    th_player.join()
    audio.stop()

except KeyboardInterrupt:
    if th_tui.is_alive():
        tui_q.put(['quit', None, None])
        th_tui.join()

    if th_web.is_alive():
        th_web.join()

    if th_player.is_alive():
        player_q.put('quit')
        th_player.join()

    if audio is not None:
        audio.stop()
