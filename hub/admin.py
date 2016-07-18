import os
import cherrypy

from nx import *
from .admin_base import NebulaBaseAdmin
from .admin_browser import admin_browser
from .admin_rundown import admin_rundown

class NebulaAdmin(NebulaBaseAdmin):
    @cherrypy.expose
    def index(self):
        context = self.context()
        if not context["user"]:
            return self.render("login", **context)
        context = admin_browser(context)
        return self.render("browser", **context)

    @cherrypy.expose
    def browser(self, *args, **kwargs):
        context = self.context()
        if not context["user"]:
            return self.render("login", **context)
        context = admin_rundown(context, *args, **kwargs)
        return self.render("browser", **context)

    @cherrypy.expose
    def rundown(self, *args, **kwargs):
        context = self.context()
        if not context["user"]:
            return self.render("login", **context)
        context = admin_rundown(context, *args, **kwargs)
        return self.render("rundown", **context)

    @cherrypy.expose
    def scheduler(self):
        context = self.context()
        if not context["user"]:
            return self.render("login", **context)
        #TODO: do the rest here
        return self.render("scheduler", **context)

    @cherrypy.expose
    def jobs(self):
        context = self.context()
        if not context["user"]:
            return self.render("login", **context)
        #TODO: do the rest here
        return self.render("jobs", **context)

    @cherrypy.expose
    def services(self):
        context = self.context()
        if not context["user"]:
            return self.render("login", **context)
        #TODO: do the rest here
        return self.render("config", **context)

    @cherrypy.expose
    def config(self):
        context = self.context()
        if not context["user"]:
            return self.render("login", **context)
        #TODO: do the rest here
        return self.render("config", **context)
