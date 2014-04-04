#!/usr/bin/env python
# -*- coding: utf-8 -*-


from nx import *
from nx.assets import *
from nx.items import *

from caspar import Caspar

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi
import thread

from nx.plugins import plugin_path
import imp

class PlayoutPlugins():
    def __init__(self, channel):
        self.plugins = []
        bpath = os.path.join(plugin_path, "playout")
        if not os.path.exists(bpath):
            logging.warning("Playout plugins directory does not exist")
            return 

        for fname in os.listdir(bpath):
            mod_name, file_ext = os.path.splitext(fname)
            if file_ext != ".py":
                continue

            py_mod = imp.load_source(mod_name, os.path.join(bpath, fname))

            if not "__manifest__" in dir(py_mod):
                logging.warning("No plugin manifest found in {}".format(fname))
                continue

            if not "Plugin" in dir(py_mod):
                logging.warning("No plugin class found in {}".format(fname))
            
            logging.info("Initializing plugin {} on channel {}".format(py_mod.__manifest__["name"], channel.ident ))
            self.plugins.append(py_mod.Plugin(channel))    
        
    def __getitem__(self, key):
        return self.plugins[key]



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

    def result(self, r):
        response, data = r
        self._do_headers(response=response)
        if data:
            self._echo(json.dumps(data))
        else:
            self._echo("false")

    def error(self,response):
        self._do_headers(response=response)

    def do_GET(self):
        service = self.server.service
        self.result(service.stat())

    def do_POST(self):
        service = self.server.service
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))

        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.getheader('content-length'))
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
        
        if   method == "take":    self.result(service.take(params))
        elif method == "cue":     self.result(service.cue(params)) 
        elif method == "freeze":  self.result(service.freeze(params)) 
        elif method == "retake":  self.result(service.retake(params)) 
        elif method == "abort":   self.result(service.abort(params))
        elif method == "stat":    self.result(service.stat(params))
        elif method == "cg_list": self.result(service.cg_list(params))
        elif method == "cg_exec": self.result(service.cg_exec(params))
        
        else:
            self.error(501) # Not implemented
        



class Service(ServicePrototype):
    def on_init(self):
        if not config["playout_channels"]:
            logging.error("No playout channel configured")
            self.shutdown()

        self.caspar = Caspar()
        for id_channel in config["playout_channels"]:
            channel_cfg = config["playout_channels"][id_channel]

            logging.debug("Initializing playout channel {}: {}".format(id_channel, channel_cfg["title"]))

            channel = self.caspar.add_channel(channel_cfg["caspar_host"], 
                                              channel_cfg["caspar_port"], 
                                              channel_cfg["caspar_channel"], 
                                              channel_cfg["feed_layer"], 
                                              id_channel
                                             )

            channel.playout_spec  = channel_cfg["playout_spec"]
            channel.on_main       = self.channel_main
            channel.on_change     = self.channel_change

            channel.cued_asset    = False
            channel.current_asset = False
            channel._changed      = False
            channel._last_run     = False
            channel.plugins       = PlayoutPlugins(channel)

        port = 42100

        self.server = HTTPServer(('',port), ControlHandler)
        self.server.service = self
        thread.start_new_thread(self.server.serve_forever,())



    def cue(self, params={}):
        id_channel = params.get("id_channel", False)
        id_item    = params.get("id_item", False)

        if not (id_item and id_channel):
            return 400, "Bad request"

        if not id_channel in self.caspar.channels:
            return 400, "Requested channel is not operated by this service"

        item  = Item(id_item)
        if not item:
            return 404, "No such item"

        if not item["id_asset"]:
            return 400, "Cannot cue virtual item"

        channel = self.caspar[id_channel]

        master_asset  = item.get_asset()
        id_playout = master_asset[channel.playout_spec]
        playout_asset = Asset(id_playout)

        if not os.path.exists(playout_asset.get_file_path()):
            return 404, "Playout asset is offline"

        fname = os.path.splitext(os.path.basename(playout_asset["path"]))[0].encode("utf-8")

        return channel.cue(fname, 
                           id_item = id_item
                          )




    def take(self,params={}):
        id_channel = params.get("id_channel", False)
        if not id_channel in self.caspar.channels:
            return 400, "Requested channel is not operated by this service"
        channel = self.caspar[id_channel]
        res = channel.take()
        print res
        return res

    def freeze(self,params={}):
        id_channel = params.get("id_channel", False)
        if not id_channel in self.caspar.channels:
            return 400, "Requested channel is not operated by this service"
        channel = self.caspar[id_channel]
        return channel.freeze()

    def retake(self,params={}):
        id_channel = params.get("id_channel", False)
        if not id_channel in self.caspar.channels:
            return 400, "Requested channel is not operated by this service"
        channel = self.caspar[id_channel]
        return channel.retake()

    def abort(self,params={}):
        id_channel = params.get("id_channel", False)
        if not id_channel in self.caspar.channels:
            return 400, "Requested channel is not operated by this service"
        channel = self.caspar[id_channel]
        return channel.abort()




    def stat(self,params={}):
        return "200", "stat"

    def cg_list(self,params={}):
        return "200", "cg_list"

    def cg_exec(self,params={}):
        return "200", "cg_exec"


    def stat(self):
        return "200", "Running"







    def channel_main(self, channel):

        if not channel.cued_asset and channel.cued_item:
            channel.cued_asset = Item(channel.cued_item).get_asset()

        data = {}
        data["id_channel"]    = channel.ident

        data["current_item"]  = channel.current_item
        data["cued_item"]     = channel.cued_item
        data["position"]      = channel.get_position()
        data["duration"]      = channel.get_duration()
        data["current_title"] = channel.current_asset["title"] if channel.current_asset else "(no clip)"
        data["cued_title"]    = channel.cued_asset["title"]    if channel.cued_asset    else "(no clip)"
        data["request_time"]  = channel.request_time

        messaging.send("playout_status", data)

        for plugin in channel.plugins:
            if not plugin.busy:
                thread.start_new_thread(plugin._main, ())

        if channel.current_item and not channel.cued_item and not channel._cueing:
            #self.cue_next(channel)
            thread.start_new_thread(self.cue_next, (channel,))



    def channel_change(self, channel):
        itm = Item(channel.current_item)
        channel.current_asset = itm.get_asset()

        logging.info ("Advanced to {}".format(itm) )


        self.on_change_update(channel)
        #thread.start_new_thread(self.on_change_update, (channel))
        
        for plugin in channel.plugins:
            thread.start_new_thread(plugin.on_change, ())

        

    def on_change_update(self, channel):
        db = DB()

        # Update AsRun

     #   if channel._last_run:
     #       db.query("UPDATE nebula_asrun SET stop_time = %s WHERE id_run = %s" %(int(time()) , channel._last_run_item  ))
     #   db.query("INSERT INTO nebula_asrun (id_asset,title, start_time, id_item, id_channel) VALUES (%s,'%s',%s,%s,%s) " % (channel.current_asset.id_asset, db.sanit(channel.current_asset["Title"]), int(time()), channel.current_item, channel.ident ) ) 
     #   channel._last_run_item = db.lastid()
     #   db.commit()
     #   channel._changed = False

        # Cue next item
        self.cue_next(channel, db=db)


    
    def cue_next(self, channel, id_item=False, db=False, level = 0):
        if not db:
            db = DB()

        channel._cueing = True

        if not id_item:
            id_item = channel.current_item

        item_next = get_next_item(id_item, db=db)
        logging.info("Auto-cueing {}".format(item_next))

        stat, res = self.cue({"id_item"    : item_next.id, 
                              "id_channel" : channel.ident
                            })
        if failed(stat):
            if level > 5:
                logging.error("Cue it yourself....")
                return
            logging.warning("Unable to cue {}. Trying next one.".format(item_next))
            self.cue_next(channel, id_item=item_next.id, db=db, level=level+1)
