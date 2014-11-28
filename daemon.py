#!/usr/bin/env python
 
import sys, os, time, atexit
from signal import SIGTERM
 
class NebulaDaemon:
    def __init__(self, **kwargs):
        self.stdin   = kwargs.get("stdid",  "/dev/null")
        self.stdout  = kwargs.get("stdout", "/dev/null")
        self.stderr  = kwargs.get("stderr", "/dev/null")
        self.root    = kwargs.get("root",   "/opt/nx.server")
        self.proc    = kwargs.get("proc", None)
        self.pidfile = os.path.join(self.root, "nebula.pid")

    def daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.del_pid)
        pid = str(os.getpid())
        file(self.pidfile,'w+').write("%s\n" % pid)
   

    def del_pid(self):
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    @property
    def pid(self):
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
        return pid


    def start(self):
        if self.pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)
       
        self.daemonize()
        self.run()


    def stop(self):
        pid = self.pid
        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return # not an error in a restart

        try:
            while 1:
                os.system (os.path.join(self.root,"killgroup.sh {}".format(pid)))
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                self.del_pid()
                
            else:
                print str(err)
                sys.exit(1)


    def restart(self):
        self.stop()
        self.start()


    def run(self):
        if self.proc:
            self.proc()