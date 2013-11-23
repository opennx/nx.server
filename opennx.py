#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# OpenNX Main script. Dispatch + controller 
#
#


import os
import sys
import subprocess

from nx import *
from time import *

NX_ROOT = os.path.split(sys.argv[0])[0]

if not NX_ROOT in sys.path:
    sys.path.append(NX_ROOT)

if NX_ROOT != os.getcwd():
    os.chdir(NX_ROOT)



class ServiceMonitor():
    def __init__(self):
        self.services = {}
        
        #db = dbconn()
        #db.query("SELECT id_service,pid FROM nebula_services WHERE server='%s'" % HOSTNAME)
        #for r in db.fetchall(): 
        #    self.Kill(r[1])
        #
        #db.query("UPDATE nebula_services SET state = 0 WHERE server='%s'" % HOSTNAME)
        #db.commit()
        #thread.start_new_thread(self._run,())


    def getRunningServices(self):
        result = []
        for id_service in self.services.keys():
            proc, title = self.services[id_service]
            if proc.poll() == None:
                result.append(title)
        return result

    def _run(self):
        while True:
            self._main()
            sleep(2)


    def _main(self):
        return
        #db = dbconn()
        #db.query("SELECT id_service,service_type,title,state,last_seen,pid FROM nebula_services WHERE server='%s'" % HOSTNAME)
     
        #for id_service, stype, title, state, last_seen, pid in db.fetchall():

        #   if state == STARTING: # Start service
        #    if not id_service in self.services.keys():
        #     self.logging.info("Starting service %s (%s)" % (title, id_service))
        #     try:
        #      os.chdir(os.path.join(self.nebuladir,"services",stype))
        #      cmd = "python ./%s.py %d " % (stype, id_service)
        #      self.services[id_service] = (  subprocess.Popen(cmd,shell=True), title)
        #     except:
        #      self.logging.error("Unable to start service.")
        #     else:
        #      sleep(1)

        #   elif state == KILL: # Kill service
        #    if id_service in self.services.keys():
        #     self.logging.info("Killing service %s (%s)" % (title, id_service))
        #     self.Kill(self.services[id_service][0].pid)


          ## Starting / Stopping
          #######################
          ## Real state

        #for id_service in self.services.keys():
        #   proc, title = self.services[id_service]
        #   if proc.poll() == None: continue
        #   del self.services[id_service]
        #   self.logging.warning("Service %s (%d) terminated"%(title,id_service))
        #   db.query("UPDATE nebula_services SET state = 0  WHERE id_service = %d"%(id_service))
        #   db.commit()
          
          ## Real state
          ########################
          ## Autostart
          
        #db.query("SELECT id_service, title, state, autostart FROM nebula_services WHERE server = '%s' AND state=0 AND autostart=1" % HOSTNAME)
        #for id_service, title, state, autostart in db.fetchall():
        #   if not id_service in self.services.keys():
        #    self.logging.info("AutoStarting service %s (%s)"% (title, id_service))
        #    db.query("UPDATE nebula_services SET state = 2  WHERE id_service = %d"%(id_service))
        #    db.commit()
            
        #db.close()

    
    def startService(self, id_service, title, db=False):
        logging.info("Starting service %d - %s"%(id_service, title))
        self.services[id_service] = (subprocess.Popen([python_cmd, "run_service.py", str(id_service)]), title )
    
    def stopService(self, id_service, title, db=False):
        logging.info("Stopping service %d - %s"%(id_service, title))
        #well... service should stop itself :-/

    def killService(self,pid, db=False):    
        pid = self.services[id_service][0].pid
        if pid == os.getpid() or pid == 0: 
            return
        #if PLATFORM == "Linux":
        #    os.system (os.path.join(self.nebuladir,"killgroup.sh %s 2> /dev/null"%str(pid)   ))
        #elif PLATFORM == "Windows":
        #    os.system ("taskkill /F /PID " + str(pid))




while True:
    sleep(1)