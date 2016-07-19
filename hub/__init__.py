import os
import cherrypy

from nx import *
from .hub import HubHandler

class Hub():
    def __init__(self, blocking=False):
        sessions_dir = config.get("hub_sessions_dir", "/tmp/hub_sessions_{}".format(config["site_name"]))
        if not os.path.exists(sessions_dir):
            os.makedirs(sessions_dir)

        self.is_running = False

        self.config = {
            '/': {
                'tools.staticdir.root': os.path.join(config["nebula_root"], "hub"),
                'tools.trailing_slash.on' : False,
                'tools.sessions.on': True,
                'tools.sessions.storage_type' : 'file',
                'tools.sessions.storage_path' : sessions_dir
                },
            '/static': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': "static"
                },
            }

        cherrypy.config.update({
            'server.socket_host': str(config.get("hub_host", "0.0.0.0")),
            'server.socket_port': int(config.get("hub_port", 80)),
            })

        cherrypy.engine.subscribe('start', self.start)
        cherrypy.tree.mount(HubHandler(), "/", self.config)

        cherrypy.engine.subscribe('stop', self.stop)
        cherrypy.engine.start()
        if blocking:
            cherrypy.engine.block()

    def start(self):
        self.is_running = True

    def stop(self):
        self.is_running = False

    def shutdown(self):
        cherrypy.engine.exit()
