from subprocess import Popen, DEVNULL
import shlex
import os

class AudioPipe:
    def __init__(self):
        pass

    def start(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        raw_cmd = 'bash ' + dir_path + '/stream.sh'
        cmd = shlex.split(raw_cmd)
        self.pr_stream= Popen(cmd, stdout=DEVNULL, stderr=DEVNULL)

    def stop(self):
        kill(self.pr_stream)

def kill(process):
    raw_cmd = 'pkill -P ' + str(process.pid)
    cmd = shlex.split(raw_cmd)
    Popen(cmd, stdout=DEVNULL, stderr=DEVNULL)