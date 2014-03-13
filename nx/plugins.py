from nx import *

__all__ = ["plugin_path","PlayoutPlugin"]

plugin_path = os.path.join(storages[int(config["plugin_storage"])].get_path(), config["plugin_root"])


class PlayoutPlugin(object):
    def __init__(self, channel):
        self.channel = channel
        self.id_layer = self.channel.feed_layer + 1
        self.tasks = []
        self.on_init()
        self.busy = False

    def _main(self):
        self.busy = True
        try:
            self.on_main()
        except:
            logging.error("Plugin error: {}".format(str(sys.exc_info())))
        self.busy = False

    def layer(self, id_layer=False):
        if not id_layer:
            id_layer = self.id_layer
        return "{}-{}".format(self.channel.channel, id_layer)

    def query(self, query):
        return self.channel.server.query(query)

    def on_init(self):
        pass

    def on_change(self):
        pass

    def on_main(self):
        if not self.tasks: 
            return
        if self.tasks[0](): 
            del self.tasks[0]
            return


