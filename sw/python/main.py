from threading import Thread
from queue import Queue
from multiprocessing import Process, Pipe, Pool
from si4731.streamer import streamer_main
from si4731.player import player_main
from si4731.tui import TUI_main
import os, sys


def mute():
    sys.stdout = open(os.devnull, 'w')


# Create inter Process pipes
str_pipe_parent, str_pipe_child = Pipe()

# Create streamer process
pr_streamer = Process(target=streamer_main, args=(str_pipe_child,))
pr_streamer.start()

# Wait until stream process is ready
# Useful to init TUI after yummy STDOUT initializatio of pyAudio
str_pipe_parent.recv()

# Create inter thread communication queues
player_q = Queue()
tui_q = Queue()

# Create player thread
th_player = Thread(target=player_main, args=(player_q, tui_q))
th_player.start()

# Create TUI thread
th_tui = Thread(target=TUI_main, args=(tui_q, player_q))
th_tui.start()

# Wait for threads to end
th_tui.join()
th_player.join()

# Send end signal to stream process
str_pipe_parent.send('quit')
pr_streamer.join()
