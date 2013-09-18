#!/usr/bin/env python
# -*- coding: utf-8 -*-

import config
import socket, json

from time import *


class Db():
 def __init__(self):
  pass

 def __connect(self):  
  pass
  
 def query(self,q):
  pass
 
 def fetchall(self):
  pass
 
 def lastid (self):
  pass
  



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






class Cache():
 def __init__(self):
  pass
  
  
 


db        = Db()
messaging = Messaging()
logging   = Logging()  
cache     = Cache()
