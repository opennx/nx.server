from nx import *
from nx.objects import *


r = {
    "can/mcr" : config["playout_channels"].keys(),
    "can/rundown_edit" : config["playout_channels"].keys(),

    "can/view" : range(0,10),
    "can/asset_edit" : range(0,15),
    "can/asset_create" : range(0,15),
    
    "can/action" : range(0,5),
    "can/service_control" : range(0,20)
    }

# TODO: Use memcache for this
class Sessions():
    def __init__(self):
        self.data = {}

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        db = DB()
        db.query("SELECT id_user FROM nx_sessions WHERE key=%s", [key])
        try:
            user = User(db.fetchall()[0][0])
            user.meta.update(r)
            return user
        except IndexError:
            return False



sessions = Sessions()

