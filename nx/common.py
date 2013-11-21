#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import socket
import json

from time import *


########################################################################
## Constants

# Asset type
VIDEO = 0
AUDIO = 1
IMAGE = 2
TEXT  = 3

# Asset subtype
FILE      = 0
VIRTUAL   = 1

# Asset status
OFFLINE  = 0   # 
ONLINE   = 1   # 
CREATING = 2   #  
TRASHED  = 3   #  
RESET    = 4   # Reset metadata action has been invoked. Meta service will update asset metadata.

# Meta classes

NUMERIC  = 0   # Any integer of float number. 'min', 'max' and 'step' values can be provided in config
TEXT     = 1   # Single-line plain text
BLOB     = 2   # Multiline text. 'syntax' can be provided in config
DATE     = 3   # Date information. Stored as timestamp, presented as YYYY-MM-DD or calendar
TIME     = 4   # Clock information Stored as timestamp, presened as HH:MM #TBD
DATETIME = 5   # Date and time information. Stored as timestamp
TIMECODE = 6   # Timecode information, stored as float(seconds), presented as HH:MM:SS.CS (centiseconds)
DURATION = 7   # Similar as TIMECODE, Marks and subclips are visualised 
REGION   = 8   # Single time region stored as ///// TBD
REGIONS  = 9   # Multiple time regions stored as json {"region_name":(float(start_second),float(end_second), "second_region_name":(float(start_second),float(end_second)}
SELECT   = 10  # Select box
COMBO    = 11  # Similar to SELECT. Free text can be also provided instead of predefined options
FOLDER   = 12  # Folder selector. Stored as int(id_folder), Represented as text / select. including color etc.



## Constants
########################################################################


def critical_error(message):
 logging.error(message)
 sys.exit(-1)


########################################################################
## Config

class Config(dict):
  def __init__(self):
    super(Config, self).__init__()
    self["host"] = socket.gethostname()  # Machine hostname
    self["user"] = "CORE" # Service identifier. Should be overwritten by service/script.

    try:
      local_settings = json.loads(open("local_settings.json").read())
    except:
      critical_error("Unable to open site_settings file.")
    self.update(site_settings)


  def load_site_settings(self):
    """Should be called after db initialisation"""


config = Config()


## Config
########################################################################
## Database

if config['db_driver'] == "postgres": 
    import psycopg2
 
    class DB():
        def __init__(self):
            self._connect()

        def _connect(self):  
            self.conn = psycopg2.connect(database=config['db_name'], host=config['db_host'], user=config['db_user'],password=config['db_pass']) 
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


elif config['db_driver'] == "sqlite":
    class DB():
        # Not implemented
        pass
 
 
else:
    critical_error("Unknown DB Driver. Exiting.")

 
 
## Database
########################################################################
## Messaging


class Messaging():
 def __init__(self):
  self.MCAST_ADDR = "224.168.2.9"
  self.MCAST_PORT = 42112
  self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
  self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
  
 def send(self, method, data=None):
  """
  message = [timestamp, site_name, host, method, DATA] 
  """
  self.sock.sendto(json.dumps([time(), config.site_name, config.host, method, data]), (self.MCAST_ADDR,self.MCAST_PORT) )
  

## Messaging
########################################################################
## Logging


class Logging():
 def __init__(self):
  pass

 def __send(self,msgtype,message):
  messaging.send("LOG",[config['user'], msgtype, message])
  print config['user']], msgtype, message

 def debug   (self,msg): self.__send("DEBUG",msg) 
 def info    (self,msg): self.__send("INFO",msg) 
 def warning (self,msg): self.__send("WARNING",msg) 
 def error   (self,msg): self.__send("ERROR",msg) 
 def goodnews(self,msg): self.__send("GOODNEWS",msg) 
 
 

## Logging
########################################################################
## Cache

if config.cache_driver == "memcached":
 class Cache():
  def __init__(self):
   pass

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
  
 def path(self,rel=False):
  return 
  
  
class Storages():
 def __init__(self):
  self.refresh()
 
 def refresh(self):
  pass
  
  
## Filesystem
########################################################################
## Init


messaging = Messaging()
logging   = Logging()  
cache     = Cache()
storages  = Storages()


