#!/usr/bin/env python
# -*- coding: utf-8 -*-


from nx import *
from nx.assets import *

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import ssl
import cgi
import thread

from string import Template

########################################################################################################

def meta_format(key, value):
    if not key in meta_types:
        return value
    mtype = meta_types[key]

    if key == "status":
        return ['<span class="label label-danger">Offline</span>',
                '<span class="label label-info">Online</span>',
                '<span class="label label-warning">Creating</span>',
                '<span class="label label-default">Trashed</span>',
                '<span class="label label-warning">Reset</span>'][value]

    if key == "state":
        return ['<span class="label label-warning">New</span>',
                '<span class="label label-success">Approved</span>',
                '<span class="label label-danger">Declined</span>'][value]

    elif mtype.class_ in [TEXT, BLOB]:         return value
    elif mtype.class_ in [INTEGER, NUMERIC]:   return ["%.3f","%d"][float(value).is_integer()] % value
    elif mtype.class_ == DATE:                 return time.strftime("%Y-%m-%d",time.localtime(value))
    elif mtype.class_ == TIME:                 return time.strftime("%H:%M",time.localtime(value))
    elif mtype.class_ == DATETIME:             return time.strftime("%Y-%m-%d %H:%M",time.localtime(value))
    elif mtype.class_ == FILESIZE:
        for x in ['bytes','KB','MB','GB','TB']:
            if value < 1024.0: return "%3.1f&nbsp;%s" % (value, x)
            value /= 1024.0

    else: 
        return "<i>%s</i>"%value


########################################################################################################


MENU_ITEMS = [("dashboard","Dashboard"),
              ("browser","Browser"),
              ("services","Services"),
              ("porn","Porn")
             ]


class View():
    def __init__(self, template_dir='', lang='en-US'):
        self.template_dir = template_dir
        self.template = "base.tpl"
        self.lang = lang
        self.data = {}
        self["header"] = "Something"

    def __setitem__(self, key, value):
        self.data[key] = value.encode("utf-8")

    def __getitem__(self,key):
        return self.data[key]

    def render(self):
        self["title"] =  "%s - OpenNX (%s)" % (self["header"], config["site_name"])
        template = Template(open(os.path.join(self.template_dir,self.template)).read())
        return template.safe_substitute(self.data)

    def restart(self):
        self["title"] = ""
        self.template = "redirect_home.tpl"

    def dashboard(self):
        self["header"]  = "Dashboard"
        self["content"] = "here will be something"

    def browser(self):
        self["header"] = "Browser"
        start_time = time.time()
        cols = ["id_object", "title", "role/performer", "album", "genre/music", "rights", "status"]
        main = "<tr><th>&nbsp</th>%s</tr>\n" % "".join("<th>%s</th>" % meta_types[col].alias(self.lang) for col in cols)
        db = DB()
        db.query("SELECT id_asset FROM nx_assets")
        for id_asset, in db.fetchall():
            asset = Asset(id_asset)
            main += "<tr><td>%s</td>%s</tr>\n" % (
                    "<i class='fa fa-%s'></i>" % ["file-text-o", "video-camera", "volume-up", "picture-o"][asset["content_type"]], 
                    "".join("<td>%s</td>" % meta_format(col,asset[col]) for col in cols)
                    )
        self["content"] = "<table class='table table-striped table-condensed table-responsive'>\n%s</table><br> Generated in %.3f seconds" % (main, time.time()-start_time)

    def services(self):
        cols = ["id_service", "agent", "title", "host"]
        main = "<tr>%s</tr>\n" % "".join("<th>%s</th>"%col for col in cols)
        db = DB()
        db.query("SELECT id_service, agent, title, host, autostart, loop_delay, settings, state, pid, last_seen FROM nx_services")
        for id_service, agent, title, host, autostart, loop_delay, settings, state, pid, last_seen in db.fetchall():
            main += "<tr>%s</tr>\n" % "".join("<td>%s</td>" % col for col in  [id_service, agent, title, host])
        self["content"] = "<table class='table table-striped table-condensed table-responsive'>%s</table>" % main








class AdminHandler(BaseHTTPRequestHandler):
    def log_request(self, code='-', size='-'): 
        pass 
       
    def _do_headers(self,mime="text/html",response=200,headers=[]):
        self.send_response(response)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        for h in headers:
            handler.send_header(h[0],h[1])
        self.send_header('Content-type', mime)
        self.end_headers()
         
    def _echo(self,istring):
        self.wfile.write(istring)

    def result(self, obj):
        self._do_headers()
        if type(obj) in [str, unicode]:
            self._echo(obj)
        elif type(obj) in (dict, list):
            self._echo(json.dumps(obj))

    def error(self,response):
        self._do_headers(response=response)
        self._echo("Error %d" % response)


    def do_GET(self):
        service = self.server.service
        path = self.path[1:]
        if path.startswith("static"):
            fname = os.path.join(service.root_path, path) # this is very secure :-).... FIXME FIXME FIXME FIXME!!!!
            fname = fname.split("?")[0]
            if not os.path.exists(fname): 
                self.error(404)
                return
            else:
                mimes = {
                        ".png":"image/png",
                        ".jpg":"image/jpeg",
                        ".css":"text/css",
                        ".js" :"application/javascript",
                    }

                self._do_headers(mime=mimes.get(os.path.splitext(fname)[1], "text/html" ))
                self._echo(open(fname).read())
                return

        view = View(template_dir = os.path.join(service.root_path,"templates"))

        menu_item_base =  '<li class="{cls}"><a href="/{p}">{t}</a></li>'
        view["menu"]   = "".join(menu_item_base.format(cls="",p=item[0], t=item[1]) for item in MENU_ITEMS)


        if path == "restart":
            view.restart()                             
            service.soft_stop()
            
        elif path.startswith("browser"):
            view.browser()
            
        elif path.startswith("services"):
            view.services()

        elif path in ["","dashboard"]:
            view.dashboard()

        else:
            self.error(404)  
            return  
                            
        self.result(view.render())







class Service(ServicePrototype):
    def on_init(self):
        self.root_path = os.path.join(__path__[0])
        cert_name = os.path.join(self.root_path,"cert","server.pem")
        use_ssl = os.path.exists(cert_name)
        
        self.server = HTTPServer(('',8080), AdminHandler)
        if use_ssl:
            self.server.socket = ssl.wrap_socket (self.server.socket, certfile=cert_name, server_side=True)
        
        self.server.service = self
        thread.start_new_thread(self.server.serve_forever,())

    def on_main(self):
        pass