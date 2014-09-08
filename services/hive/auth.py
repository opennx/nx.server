from nx import *
from nx.objects import *

# TODO: Use memcache for this
class ActiveSessions():
    def __init__(self):
        self.data = {}

    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        db = DB()
        db.query("SELECT id_user FROM nx_sessions WHERE key=%s", [key])
        try:
            return User(db.fetchall()[0][0])
        except IndexError:
            return False

active_sessions = ActiveSessions()





def get_rights(auth_key, right=False):
    if not active_sessions[auth_key]:
        return False

    default_rights = {
        "can/mcr" : [],               # (list of channels) - User can control playback of these channels
        "can/rundown_edit" : [],      # (list of channels) - 

        "can/view" : [],              # (list of views)
        "can/asset_edit" : [],        # (list of folders)  - User can edit assets in these folders
        "can/asset_create" : [],      # (list of folders)  - User can create asset in these folder (and can move assets which they can edit to this folders)
        "can/action" : [],            # (list of actions)  - User can start this type of action

        "can/service_control" : [],   # (list of services) - User can start/stop this service
        "can/service_edit" : []       # (list of services) - User can modify this service's settings
        }

    if True: # debug only: admin
        r = {
            "can/mcr" : config["playout_channels"].keys(),
            "can/rundown_edit" : config["playout_channels"].keys(),

            "can/view" : range(0,10),
            "can/asset_edit" : range(0,15),
            "can/asset_create" : range(0,15),
            
            "can/action" : range(0,5),
            "can/service_control" : range(0,20)
            }

    default_rights.update(r)
    if right:
        return default_rights.get(right, False)
    return default_rights