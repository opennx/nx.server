#!/usr/bin/env python

from nx import *
from nx.assets import *

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi
import thread

from collections import defaultdict

########################################################################################################
## Override Metatypes human-readable formating

from nx.assets import MetaTypes as MT

class MetaTypes(MT):
    def read_format(self, key, value):
        if not key in self:
            return value
        mtype = self[key]

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

        elif mtype.class_ in [TEXT, BLOB]:         return value.encode("utf-8")
        elif mtype.class_ in [INTEGER, NUMERIC]:   return ["%.3f","%d"][float(value).is_integer()] % value
        elif mtype.class_ == DATE:                 return strftime("%Y-%m-%d",localtime(value))
        elif mtype.class_ == TIME:                 return strftime("%H:%M",localtime(value))
        elif mtype.class_ == DATETIME:             return strftime("%Y-%m-%d %H:%M",localtime(value))
        elif mtype.class_ == FILESIZE:
            for x in ['bytes','KB','MB','GB','TB']:
                if value < 1024.0: return "%3.1f&nbsp;%s" % (value, x)
                value /= 1024.0

        else: return "<i>%s</i>"%value.encode("utf-8")

meta_types = MetaTypes()


########################################################################################################


MENU_ITEMS = [("dashboard","Dashboard"),
              ("browser","Browser"),
              ("services","Services"),
              ("porn","Porn")
             ]

class View():
    def __init__(self):
        pass

    def browser(self):
        start_time = time()
        cols = ["id_asset","title", "role/performer", "album", "genre/music", "status",]

        main = "<tr><th>&nbsp</th>%s</tr>\n" % "".join("<th>%s</th>" % col for col in cols)

        db = DB()
        db.query("SELECT id_asset FROM nx_assets")
        for id_asset, in db.fetchall():
            asset = Asset(id_asset)
            main += "<tr><td>%s</td>%s</tr>\n" % ("<i class='fa fa-%s'></i>" % ["file-text-o", "video-camera", "volume-up", "picture-o"][asset["content_type"]], "".join("<td>%s</td>" % meta_types.read_format(col,asset[col]) for col in cols))
        
        return "<table class='table table-striped table-condensed table-responsive'>\n%s</table><br> Generated in %.3f seconds" % (main, time()-start_time)



    def services(self):
        cols = ["id_service", "agent", "title", "host"]

        main = "<tr>%s</tr>\n" % "".join("<th>%s</th>"%col for col in cols)

        db = DB()
        db.query("SELECT id_service, agent, title, host, autostart, loop_delay, settings, state, pid, last_seen FROM nx_services")
        for id_service, agent, title, host, autostart, loop_delay, settings, state, pid, last_seen in db.fetchall():
            main += "<tr>%s</tr>\n" % "".join("<td>%s</td>" % col for col in  [id_service, agent, title, host])

        return "<table class='table table-striped table-condensed table-responsive'>%s</table>" % main




class Templater(object):
    def __init__(self, template_name):
        self.template = open(template_name).read()
        self.data = defaultdict(str)

    def __setitem__(self,key, value):
        self.data[key] = value

    def __getitem__(self,key):
        return self.data[key]

    def result(self):
        self["title"] = "OpenNX Admin (%s)" % config["site_name"]
        if "header" in self.data:
            self["title"] = "%s - %s" % (self["header"], self["title"])

        return self.template.format(self.data)


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

    def result(self,obj):
        self._do_headers()
        if type(obj) == str:
            self._echo(obj)
        elif type(obj) in (dict, list):
            self._echo(json.dumps(obj))

    def error(self,response):
        self._do_headers(response=response)
        self._echo("Error %d" % response)


    def do_GET(self):
        start_time = time()
        service = self.server.service
        path = self.path[1:]
        if path.startswith("static"):
            fname = os.path.join(service.root_path, path) # this is very secure :-).... FIXME FIXME FIXME FIXME!!!!
            fname = fname.split("?")[0]
            if not os.path.exists(fname): 
                print fname
                self.error(404)
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


        elif path == "shutdown":
            tpl = Templater(os.path.join(service.root_path,"templates","redirect_home.tpl"))                                 
            service.soft_stop()
            
        elif path.startswith("browser"):
            tpl = Templater(os.path.join(service.root_path,"templates","base.tpl"))
            view = View()
            tpl["header"]  = "Browser"
            tpl["content"] = view.browser()

        elif path.startswith("services"):
            tpl = Templater(os.path.join(service.root_path,"templates","base.tpl"))
            view = View()
            tpl["header"]  = "Services"
            tpl["content"] = view.services()

        elif path in ["","dashboard"]:
            tpl = Templater(os.path.join(service.root_path,"templates","base.tpl"))
            tpl["header"]  = "Dashboard"

        else:
            tpl = Templater(os.path.join(service.root_path,"templates","base.tpl"))
            content = "nic tu neni"
        
        
        
        
        menu_item_base =  '<li class="{cls}"><a href="/{p}">{t}</a></li>'
        tpl["menu"]   = "".join(menu_item_base.format(cls="",p=item[0], t=item[1]) for item in MENU_ITEMS)
                                 
        self.result(tpl.result())
        print "Request done in %.3f seconds" % (time() - start_time)




class Service(ServicePrototype):
    def onInit(self):
        self.root_path = os.path.join(__path__[0])

        self.server = HTTPServer(('',8080), AdminHandler)
        self.server.service = self
        thread.start_new_thread(self.server.serve_forever,())

    def onMain(self):
        pass