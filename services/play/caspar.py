#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *

import telnetlib
import thread

### If you want to use this file separately, just uncomment following lines (and comment out first import nx)
### There is an example (or should be), how to use it at the end
#
#import os, sys, subprocess, thread
#from time import *
#from xml.etree import ElementTree as ET
#class casplog():
#    def debug(self,msg)  : print "DEBUG   : %s"%msg
#    def info(self,msg)   : print "INFO    : %s"%msg
#    def warning(self,msg): print "WARNING : %s"%msg
#    def error(self,msg)  : print "ERROR   : %s"%msg
#logging = casplog()


########################################################################
## Channel stuff

def basefname(fname):
  """Platform dependent path splitter (caspar is always on win)"""
  return os.path.splitext(fname.split("\\")[-1])[0]


class CasparChannel():
    def __init__(self, server, channel):
        self.server  = server  # CasparServer class instance
        self.channel = channel # Caspar channel (that "X" integer in PLAY x-y command)
        self.fps = 25.0

        self.xstat  = "<channel>init</channel>"  
        self.chdata = {}
        
        self.current_item   = False
        self.current_fname  = False
        self.cued_item      = False
        self.cued_fname     = False
        self.paused         = False
        
        self._cueing        = False
        self.request_time   = time()
        
        self.pos = self.dur = self.fpos = self.fdur = 0
        self.cued_in = self.cued_out = self.current_in = self.current_out = 0


    def on_main():
        pass

    def on_change():
        pass


    def get_position(self): 
        return int(self.fpos - (self.current_in*self.fps))
     
    def get_duration(self): 
        dur = self.fdur
        if self.current_out > 0: dur -= dur - (self.current_out*self.fps)
        if self.current_in  > 0: dur -= (self.current_in*self.fps)
        return dur


    def cue(self, fname, mark_in=False, mark_out=False, id_item=False, layer=False, auto=True, play=False):
    
        if not id_item:  id_item = fname
        if not layer:    layer = self.feed_layer

        marks = ""
        if mark_in:  marks += " SEEK %d"   % (float(mark_in)*self.fps)
        if mark_out: marks += " LENGTH %d" % (float(mark_out)*self.fps)
        
        if play:     q = "PLAY %s-%d %s %s"     % (self.channel,layer,fname,marks)
        else:        q = "LOADBG %s-%d %s %s %s" % (self.channel,layer,fname,["","AUTO"][auto],marks)
        
        stat, res = self.server.query(q)
        
        if not stat: 
            logging.error("Unable to cue %s" % res)
            self.cued_item  = False
            self.cued_fname = False
        else:
            self.cued_item  = id_item
            self.cued_fname = fname
            self.cued_in    = mark_in
            self.cued_out   = mark_out
            self._cueing = True
            logging.info("Cueing item %s" % self.cued_item)

        return (stat,res)
     
     
    def clear(self,layer=False):
        if not layer: layer = self.feed_layer
        return self.server.query("CLEAR %d-%d" % (self.channel, layer))

    def take(self,layer=False):
        if not layer: layer = self.feed_layer
        if not self.cued_item: return (False, "Unable to take. No item is cued.")
        self.paused = False
        return self.server.query("PLAY %d-%d" % (self.channel, layer))
    
    def retake(self,layer=False):
        if not layer: layer = self.feed_layer
        seekparam = "%s" % (int(self.current_in*self.fps))
        if self.current_out: seekparam += " LENGTH %s" % (int(self.current_out*self.fps))
        q = "PLAY %d-%d %s SEEK %s"%(self.channel, layer, self.current_fname,  seekparam)
        self.paused = False
        return self.server.query(q)
     

    def freeze(self,layer=False):
        if not layer: layer = self.feed_layer
        if not self.paused:
         q = "PAUSE %d-%d"%(self.channel,layer)
        else:
         if self.current_out: LEN = "LENGTH %s" %int(self.current_out*self.fps)
         else:                LEN = ""
         q = "PLAY %d-%d %s SEEK %s %s"%(self.channel, layer, self.current_fname, self.fpos, LEN)
       
        res,data = self.server.query(q)
        if res["status"] == "OK": self.paused = not self.paused
        return [res,data]


    def abort(self,layer=False):
        if not layer: layer = self.feed_layer
        if not self.cued_item: return [{"status":"FAILED","reason":"Unable to abort. No item is cued."},False]
        self.Take()
        sleep(.1)
        self.Freeze()
        return [{"status":"OK","reason":"Clip aborted"},True]




    def update_stat(self):
        stat, res = self.server.query("INFO %d" % self.channel)
        request_time = time()
        if not stat: 
            return False
        try:    
            xstat = ET.XML(res)
        except: 
            return False
        else:   
            self.request_time = time()
            self.xstat = xstat
            return True


    def main(self):   
        # Which layer is for video fill?
        try: 
           for layer in self.xstat.find("stage").find("layers").findall("layer"):
              if int(layer.find("index").text) != self.feed_layer:
                  continue
              else:
                  video_layer = layer
                  break
           else:
             raise Exception
        except:
            pass
         
        # What are we playing right now?
        try:
            fg_prod = video_layer.find("foreground").find("producer")
            if fg_prod.find("type").text == "image-producer":
                self.fpos = self.fdur = self.pos = self.dur = 0
            else:
                self.fpos = int(fg_prod.find("file-frame-number").text)
                self.fdur = int(fg_prod.find("file-nb-frames").text)
                self.pos  = int(fg_prod.find("frame-number").text)
                self.dur  = int(fg_prod.find("nb-frames").text)
            current_file = basefname(fg_prod.find("filename").text)
        except: 
            current_file = False
         
          
        # And which one's next?
        try:     
            cued_file = basefname(video_layer.find("background").find("producer").find("destination").find("producer").find("filename").text)
        except:  
            cued_file = False
        
        
        if not cued_file and current_file:
            changed = False
            if current_file == self.cued_fname:
                logging.info ("Advanced to the next item (%s)" % self.cued_item)
                self.current_item  = self.cued_item
                self.current_fname = self.cued_fname
                self.current_in    = self.cued_in
                self.current_out   = self.cued_out
                self.cued_in = self.cued_out = 0
                changed = True

            self.cued_fname = False
            self.cued_item  = False

            if self.OnChange and changed: 
                self.OnChange(self)

        elif self.cued_item and cued_file and cued_file != self.cued_fname and not self._cueing:
            logging.debug ("Cue mismatch: This is not the file which should be cued. IS: %s vs. SHOULDBE: %s" % (cued_file,self.cued_fname))
            self.cued_item = False # AutoCue should handle it

        if self._cueing: self._cueing = False
        if self.OnMain:  self.OnMain(self)


## Channel stuff... tricky
########################################################################
## Easy... should work



def server_ident(host,port):
    return "%s:%d"%(host,port)

class CasparServer():
    def __init__(self, host="localhost", port=5250):
        self.host = host
        self.port = port
        self.ident = server_ident(host,port)
        self.connect()

    def __repr__(self): 
        return self.ident

    def connect(self):
        try:    
            self.cmd_conn = telnetlib.Telnet(self.host,self.port)
            self.inf_conn = telnetlib.Telnet(self.host,self.port)
        except:
            return False
        else:
            return True
     
    def query(self,q):
        if q.startswith("INFO"):
            conn = self.inf_conn
        else:
            conn = self.cmd_conn
        
        try:
            conn.write("%s\r\n"%q)
            result = conn.read_until("\r\n").strip() 
        except:
            return (False, "Connection failed")
        
        if not result: 
            return (False, "Connection failed")
        
        try:
            if result[0:3] == "202":
                return (True, result)
            elif result[0:3] in ["201","200"]:
                result = conn.read_until("\r\n").strip()
                return (True, result)
            elif int(result[0:1]) > 3:
                return (False, result)
        except:
            return (False, "Malformed result")
        return (False, "Very strange result")

class Caspar():
    def __init__(self):
      self.servers  = {}
      self.channels = {} 
      self.bad_requests  = 0 
      thread.start_new_thread(self._start,())

    def add_channel(self, host, port, channel, feed_layer, ident):
      """
      Appends an output channel.
      Arguments:
      host, port : connection to running CasparCG server
      channel    : caspar cg channel id 
      feed_layer : "main" caspar layer - that one with playlist.
      ident      : YOUR unique identification of the channel
      """
      self._add_server(host,port)
      self.channels[ident] = CasparChannel(self, self.servers[server_ident(host,port)], channel)
      self.channels[ident].ident = ident
      self.channels[ident].feed_layer = feed_layer
      return self.channels[ident]
    
    def _add_server(self,host,port):
        if not server_ident(host,port) in self.servers:
            self.servers[ServerIdent(host,port)] = CasparServer(self,host,port)

    def _start(self):
        while True:
            self._main()
            sleep(.2) 

    def _main(self):
        for ident in self.channels:
            channel = self.channels[ident]
            if not channel.update_stat():
                self.bad_requests += 1
                if self.bad_requests > 10:
                    logging.warning("Connection lost. Reconnecting...")
                    if channel.server.connect(): 
                        logging.goodnews("Connection estabilished")
                    else:
                        logging.error("Connection call failed")
                        sleep(2)
                sleep(.1)
                continue
            else:
                self.bad_requests = 0
                channel.Main() 


## an example of stand alone use
if __name__ == "__main__":
  pass # HA HAHAHAHA

