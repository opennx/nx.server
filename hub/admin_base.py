import os
import cherrypy
import jinja2

from nx import *

from pprint import pprint
pprint(dir(cherrypy))


class Context(dict):
    def message(self, message, level="info"):
        if not messages in self.keys():
            self["flash_messages"] = []
        self["flash_messages"].append([message, level])


class NebulaBaseAdmin(object):
    def __init__(self):
        template_root = os.path.join(config["nebula_root"], "hub", "templates")
        self.jinja = jinja2.Environment(
                loader=jinja2.FileSystemLoader(template_root)
            )

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
        return template.render(**context)

    @cherrypy.expose
    def login(self, **kwargs):
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

