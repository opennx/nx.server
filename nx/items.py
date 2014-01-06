 #!/usr/bin/env python
 # -*- coding: utf-8 -*-

from server import *
from assets import *


class Item():
    def __init__(self, id_item=False, db=False):
        self.id_item = id_item
        self.db = db
        if self.id_item:
            self._load()
        else:
            self._new()

    def _new(self):
        self.id_item  = False
        self.id_bin   = False
        self.id_asset = False
        self.position = 0
        self.params = {}
        self.asset = False


    def _load(self):
        self.data = json.loads(cache.load("A%d" % id_asset))
        if not self.db:
            self.db = DB()
        db = self.db




class Bin():
    def __init__(self, id_bin=False):
       pass



class Rundown():
     def __init__(self, date=False):
        pass




def get_bin_first_item(id_bin, db=False):
    if not db:
        db = DB()
    db.query("SELECT id_item FROM nx_items WHERE id_bin=%d ORDER BY position LIMIT 1" % id_bin)
    try:
        return db.fetchall()[0][0]
    except:
        return False

def get_next_item(id_item, db=False):
    if not db:
        db = DB()
    