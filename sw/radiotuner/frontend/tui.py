import curses
import time

def TUI_main(tui_q, player_q):

    # Initialize Terminal User Interface
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.nodelay(True)
    win = curses.newwin(32, 12, 0, 0)
    curses.curs_set(False)

    # Initialize colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    run_app=True
    while(run_app):
        char = stdscr.getch()
        if char == 261: # RIGTH ARROW
            player_q.put(['seek_up',None])
            stdscr.clear()
        if char == 260: # LEFT ARROW
            player_q.put(['seek_down',None])
            stdscr.clear()
        if char == 259: # UP ARROW
            player_q.put(['vol_up',None])
            stdscr.clear()
        if char == 258: # DOWN ARROW
            player_q.put(['vol_down',None])
            stdscr.clear()
        if char == ord('q'): # QUIT
            player_q.put(['quit',None])
            run_app = False

        while tui_q.empty() is False:
            [msg, radio, volume]= tui_q.get()
            if msg == 'radiovol':
                refresh_TUI(stdscr, radio, volume)
            if msg == 'quit':
                run_app = False

        time.sleep(0.1)

    # End APP
    stdscr.keypad(False)
    stdscr.nodelay(False)
    curses.nocbreak()
    curses.echo()
    curses.endwin()

def refresh_TUI(screen, radio, volume):
    blankline = "                                "
    screen.addstr(0, 0, "     Si4731 Radio Receiver      ", curses.A_REVERSE)

    if (radio is not None):
        screen.addstr(2, 6, "<<", curses.A_NORMAL)
        screen.addstr(2, 24, ">>", curses.A_NORMAL)
        screen.addstr(2, 11, ' ' + str(radio.station.Frequency) + ' MHz ', curses.color_pair(1) + curses.A_REVERSE)

        if(radio.rds.PS.string.isprintable()):
            screen.addstr(4,0,blankline,curses.A_NORMAL)
            screen.addstr(4, 16-int(len(radio.rds.PS.string)/2), radio.rds.PS.string, curses.color_pair(3) + curses.A_ITALIC)
        if(radio.rds.RadioTextA.string.isprintable()):
            screen.addstr(5,0,blankline,curses.A_NORMAL)
            screen.addstr(6,0,blankline,curses.A_NORMAL)
            if (len(radio.rds.RadioTextA.string) < 32):
                screen.addstr(5, 16-int(len(radio.rds.RadioTextA.string)/2), radio.rds.RadioTextA.string, curses.color_pair(2) + curses.A_NORMAL)
            else:
                RText = radio.rds.RadioTextA.string.split(maxsplit=2)
                screen.addstr(5, 16-int(len(RText[0])/2), RText[0], curses.color_pair(2) + curses.A_NORMAL)
                screen.addstr(6, 16-int(len(RText[1])/2), RText[1], curses.color_pair(2) + curses.A_NORMAL)
        screen.addstr(8, 5, "RSSI: " + str(radio.station.RSSI).zfill(2), curses.A_NORMAL)
        screen.addstr(8, 20, "SNR: " + str(radio.station.SNR).zfill(2), curses.A_NORMAL)
        screen.addstr(10, 0, "             by iz2k            ", curses.color_pair(4) + curses.A_NORMAL)
        screen.addstr(11, 0, " " + chr(9650) + chr(9660) + " use arrows " + chr(9668) + " " + chr(9658) + "       (q)quit", curses.A_REVERSE)
        print_vol(screen, volume)
        screen.refresh()

def get_vol_color_index(vol):
    idx = 4 # Green
    if vol > 4:
        idx = 5 # YELLOW
    if vol > 8:
        idx = 3 # RED
    return idx

def print_vol(screen, volume):
    # Print volume squares
    for i in range(1, 11):
        if volume/10 > (10-i):
            screen.addstr(i, 31, '#', curses.color_pair(get_vol_color_index(11-i)) + curses.A_NORMAL)

    # Print volume number
    # Caluclate vertical position
    volposv = int(11-volume/10)
    # Fix position for 0%
    if(volposv>10):
        volposv=10
    # Calculate horizontal position
    volposh = 32 - len(str(volume))
    # Print volume
    screen.addstr(volposv, volposh, str(volume), curses.color_pair(get_vol_color_index(volume/10)) + curses.A_NORMAL)
