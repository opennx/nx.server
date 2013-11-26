#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import socket
import json

from time import *
from xml.etree import ElementTree as ET

from constants import *


if __name__ == "__main__":
    sys.exit(-1)

if sys.platform == "win32":
    PLATFORM   = "windows"
    python_cmd = "c:\\python27\python.exe"
else:
    PLATFORM   = "linux"
    python_cmd = "python"

HOSTNAME = socket.gethostname()


def critical_error(message):
    try: 
        logging.error(message)
    except: 
        print "CRITICAL ERROR: %s" % message
    sys.exit(-1)


########################################################################
## Config

class Config(dict):
    def __init__(self):
        super(Config, self).__init__()
        self["host"] = socket.gethostname()  # Machine hostname
        self["user"] = "Core" # Service identifier. Should be overwritten by service/script.

        try:
            local_settings = json.loads(open("local_settings.json").read())
        except:
            critical_error("Unable to open site_settings file.")
        self.update(local_settings)

    def __getitem__(self,key):
        return self.get(key,False)

    def load_site_settings(self):
        """Should be called after db initialisation"""
        try:
            db = DB()
            db.query("SELECT key, value FROM nx_settings")
            for key, value in db.fetchall():
                self[key] = value
        except:
            print "Unable to load local settings. Nothing will work."


config = Config()


## Config
########################################################################
## Database

if config['db_driver'] == 'postgres': 
    import psycopg2
    class DB():
        def __init__(self):
            self._connect()

        def _connect(self):  
            self.conn = psycopg2.connect(database = config['db_name'], 
                                         host     = config['db_host'], 
                                         user     = config['db_user'],
                                         password = config['db_pass']
                                         ) 
            self.cur = self.conn.cursor()

        def query(self,q,*args):
            self.cur.execute(q,*args)

        def sanit(self, instr):
            #TODO: THIS SHOULD BE HEEEEAAAVILY MODIFIED
            try: return str(instr).replace("''","'").replace("'","''").decode("utf-8")
            except: return instr.replace("''","'").replace("'","''")

        def fetchall(self):
            return self.cur.fetchall()
       
        def lastid (self):
            self.query("select lastval()")
            return self.fetchall()[0][0]

        def commit(self):
            self.conn.commit()

        def rollback(self):
            self.conn.rollback()


elif config['db_driver'] == 'sqlite':
    import sqlite3
    class DB():
        def __init__(self):
            self._connect()

        def _connect(self):
            try:
                self.conn = sqlite3.connect(config["db_host"]) 
                self.cur = self.conn.cursor()
            except:
                raise Exception, "Unable to connect database."

        def query(self,q,*args):
            self.cur.execute(q,*args)

        def sanit(self, instr):
            return str(instr).replace("''","'").replace("'","''")

        def fetchall(self):
            return self.cur.fetchall()
          
        def lastid(self):
            r = self.cur.lastrowid
            return r
          
        def commit(self):
            self.conn.commit()

        def rollback(self):
            self.conn.rollback()
         
        def close(self):
            self.conn.close()


 
elif config['db_driver'] == 'null':
    class DB():
        # For testing purposes only. To be removed
        pass

else:
    critical_error("Unknown DB Driver. Exiting.")

 
## Now it's time to load rest of the settings
config.load_site_settings()

 
## Database
########################################################################
## Messaging
#
# Seismic messaging sends multicast UDP message over local network. 
# It's useful for logging, updating client views, configurations etc.
#

class Messaging():
    def __init__(self):
        self.MCAST_ADDR = config["seismic_addr"]
        self.MCAST_PORT = int(config["seismic_port"])
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
  
    def send(self, method, data=None):
        """
        message = [timestamp, site_name, host, method, DATA] 
        """
        self.sock.sendto(json.dumps([time(), config["site_name"], config["host"], method, data]), (self.MCAST_ADDR,self.MCAST_PORT) )

## Messaging
########################################################################
## Logging


class Logging():
    def __init__(self):
        pass

    def _send(self,msgtype,message):
        messaging.send("LOG",[config['user'], msgtype, message])
        print msgtype.ljust(10), config['user'].ljust(15), message

    def debug   (self,msg): self._send("DEBUG",msg) 
    def info    (self,msg): self._send("INFO",msg) 
    def warning (self,msg): self._send("WARNING",msg) 
    def error   (self,msg): self._send("ERROR",msg) 
    def goodnews(self,msg): self._send("GOOD NEWS",msg) 



## Logging
########################################################################
## Cache

if config["cache_driver"] == "memcached":
    import pylibmc

    class Cache():
        def __init__(self):
            self.site = config["site_name"]
            self.host = config["cache_host"]
            self.port = config["cache_port"]
            self.cstring = '%s:%s'%(self.host,self.port)

        def _conn(self):
            return pylibmc.Client([self.cstring])

        def load(self,key):
            try:
                conn = self._conn()
                return conn.get("%s_%s"%(self.site,key))
            except:
                return False

        def save(self,key,value):
            for i in range(10):
                try:
                    conn = self._conn()
                    val = conn.set("%s_%s"%(self.site,key),value)
                    break
                except:  
                    print "MEMCACHE SAVE FAILED %s" % key
                    print str(sys.exc_info())
                    sleep(1)
                else:
                    critical_error ("Memcache save failed. This should never happen. Check MC server")
                    sys.exit(-1)
            return val

        def delete(self,key):
            for i in range(10):
                try:
                    conn = self._conn()
                    conn.delete("%s_%s"%(self.site,key))
                    break
                except: 
                    print "MEMCACHE DELETE FAILED %s" % key
                    print str(sys.exc_info())
                    sleep(1)
                else:
                    critical_error ("Memcache delete failed. This should never happen. Check MC server")
                    sys.exit(-1)
            return True


else:
    class Cache():
        def __init__(self):
            self.data = {}   
        def load(self,key):
            return self.data.get(key,False)
        def save(self,key,value):
            self.data[key] = value

## Cache
########################################################################
## Filesystem

class Storage():
    def __init__(self): 
        pass
    def get_path(self,rel=False):
        if self.protocol == LOCAL:
            return self.path

class Storages(dict):
    def __init__(self):
        super(Storages, self).__init__()
        self.refresh()
 
    def refresh(self):
        try:
            db = DB()
            db.query("SELECT id_storage, title, protocol, path, login, password FROM nx_storages")
        except:
            print "Unable to load storages information."
            return
            
        for id_storage, title, protocol, path, login, password in db.fetchall():
            storage = Storage()
            storage.id_storage = id_storage
            storage.title      = title
            storage.protocol   = protocol
            storage.path       = path
            storage.login      = login
            storage.password   = password
            self[id_storage] = storage
            
## Filesystem
########################################################################
## Init global objects

messaging = Messaging()
logging   = Logging()  
cache     = Cache()
storages  = Storages()
