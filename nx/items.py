 #!/usr/bin/env python
 # -*- coding: utf-8 -*-

from nx.common import *
from nx.common.nxobject import NXObject
from nx.common.metadata import meta_types

from nx.assets import Asset


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
            if self.get_asset()
                return self.get_asset()[key]
            else:
                return False
        return self.meta[key]

    def mark_in(self, new_val=False):
        if new_val:
            self["mark_in"] = new_val
        return self["mark_in"]

    def mark_out(self, new_val=False):
        if new_val:
            self["mark_out"] = new_val
        return self["mark_out"]

    def get_asset(self):
        if (not self.asset) and self["id_asset"]:
            self.asset = Asset(self["id_asset"])
        return self.asset

    def get_duration(self):
        if self.id_asset == -1: 
            dur = 999999
        else:
            dur  = self.get_asset()["duration"]

        if not dur:
            return 0
            
        mark_in  = self.mark_in()
        mark_out = self.mark_out()
        if mark_out > 0: dur -= dur - mark_out
        if mark_in  > 0: dur -= mark_in
        return dur



class Bin(NXObject):
    object_type = "bin"

    def _new(self):
        self.meta = {}




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
    