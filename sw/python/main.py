from si4731.si4731 import Si4731
import curses
import time
import alsaaudio


def init_TUI():
    # Create TUI controller
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.nodelay(True)
    win = curses.newwin(32, 12, 0, 0)
    curses.curs_set(False)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    return stdscr

def kill_TUI():
    stdscr.keypad(False)
    stdscr.nodelay(False)
    curses.nocbreak()
    curses.echo()
    curses.endwin()

def get_vol_color_index(vol):
    idx = 4 # Green
    if vol > 4:
        idx = 5 # YELLOW
    if vol > 8:
        idx = 3 # RED
    return idx

def print_vol():
    volume = mixer.getvolume()[0]
    for i in range(1, 11):
        if volume/10 > (10-i):
            stdscr.addstr(i, 31, '#', curses.color_pair(get_vol_color_index(11-i)) + curses.A_NORMAL)
    if volume < 100:
        stdscr.addstr(int(10.5-volume/10), 30, str(volume), curses.color_pair(get_vol_color_index(volume/10)) + curses.A_NORMAL)
    else:
        stdscr.addstr(int(11-volume/10), 29, str(volume), curses.color_pair(get_vol_color_index(volume/10)) + curses.A_NORMAL)



def refresh_TUI():
    blankline = "                                "
    stdscr.addstr(0, 0, "     Si4731 Radio Receiver      ", curses.A_REVERSE)

    stdscr.addstr(2, 6, "<<", curses.A_NORMAL)
    stdscr.addstr(2, 24, ">>", curses.A_NORMAL)
    stdscr.addstr(2, 11, ' ' + str(radio.station.Frequency) + ' MHz ', curses.color_pair(1) + curses.A_REVERSE)

    if(radio.rds.PS.string.isprintable()):
        stdscr.addstr(4,0,blankline,curses.A_NORMAL)
        stdscr.addstr(4, 16-int(len(radio.rds.PS.string)/2), radio.rds.PS.string, curses.color_pair(3) + curses.A_ITALIC)
    if(radio.rds.RadioTextA.string.isprintable()):
        stdscr.addstr(5,0,blankline,curses.A_NORMAL)
        stdscr.addstr(6,0,blankline,curses.A_NORMAL)
        if (len(radio.rds.RadioTextA.string) < 32):
            stdscr.addstr(5, 16-int(len(radio.rds.RadioTextA.string)/2), radio.rds.RadioTextA.string, curses.color_pair(2) + curses.A_NORMAL)
        else:
            RText = radio.rds.RadioTextA.string.split(maxsplit=2)
            stdscr.addstr(5, 16-int(len(RText[0])/2), RText[0], curses.color_pair(2) + curses.A_NORMAL)
            stdscr.addstr(6, 16-int(len(RText[1])/2), RText[1], curses.color_pair(2) + curses.A_NORMAL)
    stdscr.addstr(8, 5, "RSSI: " + str(radio.station.RSSI).zfill(2), curses.A_NORMAL)
    stdscr.addstr(8, 20, "SNR: " + str(radio.station.SNR).zfill(2), curses.A_NORMAL)
    stdscr.addstr(10, 0, "             by iz2k            ", curses.color_pair(4) + curses.A_NORMAL)
    stdscr.addstr(11, 0, " " + chr(8593) + chr(8595) + " use arrows           (q)quit", curses.A_REVERSE)
    print_vol()
    stdscr.refresh()

# Initialize Terminal User Interface
stdscr = init_TUI()

mixer = alsaaudio.Mixer('Speaker')
volume = mixer.getvolume()[0]

radio=Si4731()
radio.set_volume(63)
radio.fm_tune(97.2)
radio.get_rsq_status()
refresh_TUI()

run_app=True
while(run_app):
    radio.get_rsq_status()
    char = stdscr.getch()
    if char == 261: # RIGTH ARROW
        radio.fm_seek_up()
        stdscr.clear()
    if char == 260: # LEFT ARROW
        radio.fm_seek_down()
        stdscr.clear()
    if char == 259: # UP ARROW
        if (volume<95):
            volume=volume+5
        else:
            volume=100
        mixer.setvolume(volume)
        stdscr.clear()
    if char == 258: # DOWN ARROW
        if (volume>5):
            volume=volume-5
        else:
            volume=0
        mixer.setvolume(volume)
        stdscr.clear()
    if char == ord('q'): # QUIT
        run_app = False
    if (radio.check_rds()):
        radio.get_rds_status()

    refresh_TUI()

# End APP
kill_TUI()