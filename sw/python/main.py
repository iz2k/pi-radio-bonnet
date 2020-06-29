import threading
from queue import Queue
from si4731.player import player_main
from si4731.tui import TUI_main

# Create inter thread communication queues
player_q = Queue()
tui_q = Queue()

# Create player thread
th_player = threading.Thread(target=player_main, args=(player_q, tui_q))
th_player.start()

# Create TUI thread
th_tui = threading.Thread(target=TUI_main, args=(tui_q, player_q))
th_tui.start()

th_tui.join()
th_player.join()