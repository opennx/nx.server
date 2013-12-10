#!/usr/bin/env python
# -*- coding: utf-8 -*-


from nx import *
from caspar import Caspar

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from functools import partial
import cgi


class ControlHandler(BaseHTTPRequestHandler):
    def log_request(self, code='-', size='-'): 
        pass 
       
    def _do_headers(self,mime="application/json",response=200,headers=[]):
        self.send_response(response)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        for h in headers:
            handler.send_header(h[0],h[1])
        self.send_header('Content-type', mime)
        self.end_headers()
         
    def _echo(self,istring):
        self.wfile.write(istring.encode("utf-8"))

    def result(self,obj):
        self._do_headers()
        self._echo()

    def error(self,response):
        self._do_headers(response=response)

      
    def do_GET(self):
        self.result("Hello :-)")

    def do_POST(self):
        service = self.server.service
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))

        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
        else:
            logging.debug("No post data")
            self.error(400)
            return
        
        try:
            method = postvars["method"][0]
            params = json.loads(postvars["params"][0])
        except:
            logging.debug("Malformed request")
            self.error(400)
            return
        
        if   method == "take":    self.echo(service.take(params))
        elif method == "cue":     self.echo(service.cue(params)) 
        elif method == "freeze":  self.echo(service.freeze(params)) 
        elif method == "retake":  self.echo(service.retake(params)) 
        elif method == "abort":   self.echo(service.abort(params))
        elif method == "stat":    self.echo(service.stat(params))
        elif method == "cg_list": self.echo(service.cg_list(params))
        elif method == "cg_exec": self.echo(service.cg_exec(params))
        else:
         self.error(501) # Not implemented
        return
        



class Service(ServicePrototype):
    def onInit(self):
        if not config["playout_channels"]:
            self.logging.error("No playout channel configured")
            self.shutdown()

        self.caspar = Caspar()
        for id_channel in config["playout_channels"]:
            channel_cfg = config["playout_channels"][id_channel]

            channel = self.caspar.add_channel(channel_cfg["caspar_host"], channel_cfg["caspar_port"], channel_cfg["caspar_channel"], channel_cfg["feed_layer"], id_channel)
            channel.on_main   = partial(self.channel_main, channel)
            channel.on_change = partial(self.channel_change, channel)


    def take(self,params={}):
        pass

    def cue(self,params={}):
        pass

    def freeze(self,params={}):
        pass

    def retake(self,params={}):
        pass

    def recover(self,params={}):
        pass

    def abort(self,params={}):
        pass

    def stat(self,params={}):
        pass

    def cg_list(self,params={}):
        pass

    def cg_exec(self,params={}):
        pass



    def channel_main(self,):
        pass

    def channel_change(self):
        pass