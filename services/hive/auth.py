from nx import *
from nx.objects import *

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
            return user
        except IndexError:
            return False

    def __delitem__(self, key):
        if key in self.data:
            del(self.data[key])

sessions = Sessions()
