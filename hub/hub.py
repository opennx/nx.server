import os
import cherrypy
import jinja2
import pprint

from nx import *

from .admin_dashboard import admin_dashboard
from .admin_assets import admin_assets
from .admin_rundown import admin_rundown
from .admin_scheduler import admin_scheduler
from .admin_jobs import admin_jobs
from .admin_services import admin_services
from .admin_config import admin_config


views = {
        "dashboard" : admin_dashboard,
        "assets" : admin_assets,
        "rundown" : admin_rundown,
        "scheduler" : admin_scheduler,
        "jobs" : admin_jobs,
        "services" : admin_services,
        "config" : admin_config
    }


api_headers = [
        ["Content-Type", "application/json"],
        ["Connection", "keep-alive"],
        ["Cache-Control", "no-cache"],
        ["Access-Control-Allow-Origin", "*"]
    ]

api_methods = {
        "get" : api_get,
        "rundown" : api_rundown
    }



class Context(dict):
    def message(self, message, level="info"):
        if not messages in self.keys():
            self["flash_messages"] = []
        self["flash_messages"].append([message, level])


class HubHandler(object):
    def __init__(self):
        template_root = os.path.join(config["nebula_root"], "hub", "templates")
        self.jinja = jinja2.Environment(
                loader=jinja2.FileSystemLoader(template_root)
            )

    #
    # UTILS
    #

    def context(self):
        id_user = cherrypy.session.get("id_user", 0)
        user = User(id_user) if id_user else False
        context = Context()
        context.update({
                "config" : config,
                "meta_types" : meta_types,
                "storages" : storages,
                "user" : user
            })
        return context

    def render(self, view, **context):
        template = self.jinja.get_template("{}.html".format(view))
        context["view"] = view
        js_path = os.path.join(config["nebula_root"], "hub", "static", "js", "{}.js".format(view))
        if os.path.exists(js_path):
            context["view_js"] = "/static/js/{}.js".format(view)
        return template.render(**context)

    def render_error(self, response_code, message):
        cherrypy.response.status = response_code
        return self.render("error", {"error_messsage" : message, "error_code" : response_code })

    #
    # EXPOSED
    #

    @cherrypy.expose
    def login(self, **kwargs):
        if cherrypy.request.method != "POST":
            return self.render_error(400, "Bad request")
        login = kwargs.get("login", "-")
        password = kwargs.get("password", "-")
        user = get_user(login, password)
        if user:
            cherrypy.session["id_user"] = user.id
            raise cherrypy.HTTPRedirect(kwargs.get("from_page", "/"))
        else:
            logging.error("{} login failed".format(login))
            cherrypy.session["id_user"] = False
            raise cherrypy.HTTPRedirect("/")


    @cherrypy.expose
    def logout(self, **kwargs):
        cherrypy.session["id_user"] = 0
        cherrypy.lib.sessions.expire()
        raise cherrypy.HTTPRedirect("/")


    @cherrypy.expose
    def default(self, *args, **kwargs):
        try:
            view = args[0]
            if not view in views:
                raise IndexError
        except IndexError:
            view = "dashboard"
        if args:
            args = args[1:]
        context = self.context()
        if not context["user"]:
            return self.render("login", **context)
        context = views[view](context, args, **kwargs)
        return self.render(view, **context)


    @cherrypy.expose
    def api(self, method=False):
        for h, v in api_headers:
            cherrypy.response.headers[h] = v

        if cherrypy.request.method != "POST":
            return {"response" : 400, "message" : "Bad request. Post expected."}

        cl = cherrypy.request.headers['Content-Length']
        rawbody = cherrypy.request.body.read(int(cl))
        kwargs = json.loads(rawbody)


        context = self.context()
        if not context["user"]:
            return {"response" : 401, "message" : "Not logged in"}


        if method in api_methods:
            logging.debug("Executing {} /w params {}".format(method, kwargs))
            data = api_methods[method](**kwargs)

        return json.dumps(data)
