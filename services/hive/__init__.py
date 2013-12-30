#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *
from nx.assets import *

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import ssl
import cgi
import thread

class AdminHandler(BaseHTTPRequestHandler):
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
        self.wfile.write(istring)

    def result(self, response, data):
        self._do_headers(response=response)
        if data:
            self._echo(data)
        else:
            self._echo(False)

    def do_POST(self):
        start_time = time.time()

        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.getheader('content-length'))
            postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
        else:
            logging.error("No post data")
            self.result(ERROR_BAD_REQUEST)
            return
                
        try:
            method   = postvars["method"][0]
            auth_key = postvars["auth_key"][0]
        except:
            logging.error("No method/auth")
            self.result(ERROR_BAD_REQUEST)
            return
     
        try:   
            params = json.loads(postvars["params"][0])
        except: 
            params = {}
     
        methods = self.server.service.methods
     
        if method in methods:    
            response, data = methods[method](auth_key, params)
            self.result(response, json.dumps(data))
        else:                    
            logging.error("%s not implemented" % method)
            self.result(ERROR_NOT_IMPLEMENTED,False)
            return

        logging.debug("Query %s completed in %.03f seconds" % (method, time.time()-start_time))


import hive_assets, hive_settings

class Service(ServicePrototype):
    def onInit(self):
        self.root_path = os.path.join(__path__[0])
        cert_name = os.path.join(self.root_path,"cert","server.pem")
        use_ssl = os.path.exists(cert_name)
        
        self.methods = {}

        for module in [hive_assets, hive_settings]:
            for method in dir(module):
                if not method.startswith("hive_"):
                    continue
                method_title = method.lstrip("hive_")
                module_name  = module.__name__.split(".")[-1] 
                exec ("self.methods['%s'] = %s.%s" % (method_title, module_name, method ))
        try:
            port = int(self.config.find("port").text)
        except:
            port = 42000

        logging.debug("Starting hive at port %d" % port)

        self.server = HTTPServer(('',port), AdminHandler)
        if use_ssl:
            self.server.socket = ssl.wrap_socket (self.server.socket, certfile=cert_name, server_side=True)
        
        self.server.service = self
        thread.start_new_thread(self.server.serve_forever,())


    def onMain(self):
        pass