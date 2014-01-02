#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# OpenNX Main script. Dispatch + controller 
#
#

import os
import sys
import subprocess
import thread

from nx import *
from nx.shell import shell



class StorageMonitor():
    def __init__(self,once=False):
        if once: 
            self._main()
        else:    
            thread.start_new_thread(self._run,())

    def _run(self):
        while True:
            self._main()
            time.sleep(60)

    def _main(self):
        for id_storage in storages:
            storage = storages[id_storage]
            if ismount(storage.get_path()): 
                try:
                    f = open(os.path.join(storage.get_path(),".nebula_root"),"w")
                    f.write("%s:%s"%(config["site_name"],storage.id_storage))
                    f.close()
                except: 
                    pass
                continue

            logging.info ("Storage %s (%s) is not mounted. Remounting."%(storage.id_storage,storage.title))

            if not os.path.exists(storage.get_path()):
                try:     
                    os.mkdir(storage.get_path())
                except:  
                    logging.error("Unable to create mountpoint for storage %s (%s)"%(storage.id_storage,storage.title))   
                    continue
            
            self.mount(storage.protocol, storage.path, storage.get_path(), storage.login, storage.password)
            
            if ismount(storage.get_path()):     
                logging.goodnews("Storage %s (%s) remounted successfully"%(storage.id_storage,storage.title))
            else:                     
                logging.warning ("Storage %s (%s) remounting failed"%(storage.id_storage,storage.title)) 


    def mount(self, protocol, source, destination, username="", password=""):
        if protocol == CIFS:
         
            if username and password:
                credentials = ",username="+username+",password="+password
            else:
                credentials = ""
         
            host = source.split("/")[2]
            cmd = "mount -t cifs %s %s -o 'rw, iocharset=utf8, file_mode=0666, dir_mode=0777%s'" % (source,destination,credentials)

        elif protocol == NFS:
            cmd = "mount -t nfs %s %s"%(source,destination) 
         
        elif protocol == FTP:
            cmd = "curlftpfs -o umask=0777,allow_other,direct_io %s:%s@%s %s"%(username,password,source,destination)
            
        else:
            return  

        shell(cmd) 






class ServiceMonitor():
    def __init__(self):
        self.services = {}
        db = DB()
        db.query("SELECT id_service,pid FROM nx_services WHERE host='%s'" % HOSTNAME)
        for id_service, pid in db.fetchall(): 
            if pid:
                self.Kill(r[1])
        db.query("UPDATE nx_services SET state = 0 WHERE host='%s'" % HOSTNAME)
        db.commit()

        thread.start_new_thread(self._run,())
        
    def get_running_services(self):
        result = []
        for id_service in self.services.keys():
            proc, title = self.services[id_service]
            if proc.poll() == None:
                result.append((id_service, title))
        return result

    def _run(self):
        while True:
            self._main()
            time.sleep(1)

    def _main(self):
        db = DB()
        db.query("SELECT id_service, agent, title, autostart, loop_delay, settings, state, pid FROM nx_services WHERE host='%s'" % HOSTNAME)
     
        for id_service, agent, title, autostart, loop_delay, settings, state, pid in db.fetchall():
            if state == STARTING: # Start service
                if not id_service in self.services.keys():
                    self.start_service(id_service, title, db = db)

            elif state == KILL: # Kill service
                if id_service in self.services.keys():
                    self.kill_service(self.services[id_services][0].pid)

        ## Starting / Stopping
        #######################
        ## Real state

        for id_service in self.services.keys():
            proc, title = self.services[id_service]
            if proc.poll() == None: continue
            del self.services[id_service]
            logging.warning("Service %s (%d) terminated"%(title,id_service))
            db.query("UPDATE nx_services SET state = 0  WHERE id_service = %d"%(id_service))
            db.commit()
          
        ## Real state
        ########################
        ## Autostart
          
        db.query("SELECT id_service, title, state, autostart FROM nx_services WHERE host = '%s' AND state=0 AND autostart=1" % HOSTNAME)
        for id_service, title, state, autostart in db.fetchall():
            if not id_service in self.services.keys():
                logging.info("AutoStarting service %s (%s)"% (title, id_service))
                self.start_service(id_service, title)
            
    def start_service(self, id_service, title, db=False):
        logging.info("Starting service %d - %s"%(id_service, title))
        self.services[id_service] = (subprocess.Popen([python_cmd, "run_service.py", str(id_service)]), title )
        # PID & Heartbeat should be updated by run_service py
    
    def stop_service(self, id_service, title, db=False):
        logging.info("Stopping service %d - %s"%(id_service, title))
        #well... service should stop itself :-/

    def kill_service(self,pid):    
        pid = self.services[id_service][0].pid
        if pid == os.getpid() or pid == 0: 
            return
        if PLATFORM == "linux":
            os.system (os.path.join(NX_ROOT,"killgroup.sh %s 2> /dev/null"%str(pid)   ))
        elif PLATFORM == "windows":
            os.system ("taskkill /F /PID %s" % pid)






if __name__ == "__main__":
    NX_ROOT = os.path.split(sys.argv[0])[0]
    
    if not NX_ROOT in sys.path:
        sys.path.append(NX_ROOT)
    
    if NX_ROOT != os.getcwd():
        os.chdir(NX_ROOT)

    storage_monitor = StorageMonitor()
    service_monitor = ServiceMonitor()
    while True:
        time.sleep(1)