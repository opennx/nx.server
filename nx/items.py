 #!/usr/bin/env python
 # -*- coding: utf-8 -*-

from common import *
from assets import *


class Item():
    def __init__(self, id_item=False, db=False):
        self.id_item = id_item
        self.db = db
        elif self.id_asset:
            self._load(self.id_asset,db)
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
        if not self.db:
            self.db = DB()
        db = self.db




class Bin():
    def __init__(self, id_bin=False):
       pass



class Rundown():
     def __init__(self, date=False):
        pass
