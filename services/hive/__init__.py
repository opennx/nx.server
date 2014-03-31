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

    def do_GET(self):
        #TODO: This should be done better
        self._do_headers(mime="text/txt", response=200)

        logging.debug("HTTP Push client connected")

        self.site_name = config["site_name"]
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("0.0.0.0",int(config["seismic_port"])))
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        status = self.sock.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,socket.inet_aton(config["seismic_addr"]) + socket.inet_aton("0.0.0.0"));
        self.sock.settimeout(1)
    

        try:
            while True:
                try:
                    message, addr = self.sock.recvfrom(1024)
                except (socket.error):
                    continue

                try:
                    tstamp, site_name, host, method, data = json.loads(message)
                except:
                    logging.warning("Malformed seismic message detected: {}".format(message))

                if site_name == config["site_name"]:
                    self._echo("{}\n".format(message.replace("\n","")))

        except (ConnectionAbortedError, ConnectionResetError):
            logging.debug("HTTP Push client disconnected")




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




import hive_assets, hive_system, hive_items



class Service(ServicePrototype):
    def on_init(self):
        self.root_path = os.path.join(__path__[0])
        cert_name = os.path.join(self.root_path,"cert","server.pem")
        use_ssl = os.path.exists(cert_name)
        
        self.methods = {}

        for module in [hive_assets, hive_system, hive_items]:
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


    def on_main(self):
        pass