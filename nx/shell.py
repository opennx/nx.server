#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import os
import sys
import json
import uuid
import tempfile
import time

#
# Please rewrite me!
# * I want to be multiplatform
# * I want to be simple
# * I don't want to crash
#

def get_tempname():
    dr = tempfile.gettempdir()
    fn = uuid.uuid1()
    return os.path.join(dr,str(fn))


class shell():
    def __init__(self, cmd):
        """Believe or not, using temp files is much more stable than subprocess library. Especially on windows."""
        self.out_fn = get_tempname()
        self.err_fn = get_tempname()
        self._exec("%s > %s 2> %s" % (cmd, self.out_fn, self.err_fn))

    def _exec(self, cmd):
        proc = subprocess.Popen(cmd, shell=True)
        while proc.poll() == None:
            time.sleep(.1)
        return proc.poll()

    def stdout(self):   
        return open(self.out_fn)

    def stderr(self):
        return open(self.err_fn)
    



def audio_analyze(fname):
    cmd = "ffmpeg -i \"%s\" -filter_complex ebur128 -vn -f null -" % fname
    proc = shell(cmd)
    ms = []
    for line in proc.stderr().readlines():
        line = line.strip()

        if line.startswith("[Parsed_ebur128_0"):
            try:    m = float(line.split("M: ")[1].split()[0])
            except: pass
            else:   
                val = 256 + 256*max(m/80.0,-1)
                ms.append(str(val))
             #   val = (abs(m)/20.0)

    f = open ("loud","w")
    f.write("\n".join(ms))
    f.close()
