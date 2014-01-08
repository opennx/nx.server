 #!/usr/bin/env python
 # -*- coding: utf-8 -*-
from nx import *

from nxobject import NXObject
from metadata import meta_types
from assets import Asset


class Item(NXObject):
    object_type = "item"

    def _new(self):
        self["id_object"] = False
        self["id_bin"]    = False
        self["id_asset"]  = False
        self["position"]  = 0
        self.asset        = False

    def __getitem__(self, key):
        key = key.lower().strip()
        if not key in self.meta:
            if not self.asset:
                if self["id_asset"]:
                    self.asset = Asset(self["id_asset"])
                else:
                    return meta_types.format_default(key)
            if not key in self.asset.meta:
                return meta_types.format_default(key)
            return self.asset[key]
        return self.meta[key]





class Bin(NXObject):
    object_type = "bin"



class Rundown(object):
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
    