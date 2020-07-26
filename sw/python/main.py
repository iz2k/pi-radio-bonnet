from threading import Thread
from queue import Queue
from si4731.streamer import AudioPipe
from si4731.player import player_main
from si4731.tui import TUI_main

# Create inter thread communication queues
player_q = Queue()
tui_q = Queue()

# Create streamer
audio = AudioPipe()
audio.start()

# Create player thread
th_player = Thread(target=player_main, args=(player_q, tui_q))
th_player.start()

# Create TUI thread
th_tui = Thread(target=TUI_main, args=(tui_q, player_q))
th_tui.start()

# Wait for threads to end
th_tui.join()
th_player.join()
audio.stop()