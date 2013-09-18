#!/usr/bin/env python
# -*- coding: utf-8 -*-

import config
import socket, json

from time import *


########################################################################
## Constants

# Asset type
VIDEO = 1
AUDIO = 2
IMAGE = 3
XML   = 4

# Asset subtype
FILE      = 1
VIRTUAL   = 2
COMPOSITE = 3

# Asset status
ONLINE   = 1
OFFLINE  = 2
CREATING = 3
TRASHED  = 4
RESET    = 5



## Constants
########################################################################
## Database

if config.db_driver == "postgres":
 import psycopg2
 
 class Db():
  def __init__(self):
   self.__connect()

  def __connect(self):  
   try:
    self.conn = psycopg2.connect(database=config.db_name, host=config.db_host, user=config.db_user,password=config.db_pass) 
    self.cur = self.conn.cursor()
   except:
    raise Exception, "Unable to connect database."
   
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


elif config.db_driver == "sqlite":
 import sqlite3

 class Db():
  def __init__(self):
   self.__connect()
    
  def __connect(self):  
   try:
    self.conn = sqlite3.connect(config.db_host) 
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
   self.query("select lastval()")
   return self.fetchall()[0][0]
  
  def commit(self):
   self.conn.commit()
 
  def close(self):
   self.conn.close()
 
 
else:
 print "Unknown DB Driver. Exiting."
 sys.exit(-1)
 
 
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
  messaging.send("LOG",[config.user, msgtype, message])
  print config.user, msgtype, message

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

elif config.cache_driver == "internal":
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


db        = Db()
messaging = Messaging()
logging   = Logging()  
cache     = Cache()
storages  = Storages()



def CriticalError(message):
 logging.error(message)
 sys.exit(-1)
