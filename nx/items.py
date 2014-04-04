 #!/usr/bin/env python
 # -*- coding: utf-8 -*-

from nx.common import *
from nx.common.nxobject import NXObject
from nx.common.metadata import meta_types

from connection import *

from nx.assets import Asset



class EmptyAsset():
    def __init__(self):
        self.meta = {}
    def __getitem__(self, key):
        return ""

class Item(NXObject):
    object_type = "item"
    asset = None

    def _new(self):
        self["id_bin"]    = False
        self["id_asset"]  = False
        self["position"]  = 0

    def __getitem__(self, key):
        key = key.lower().strip()
        if key == "id_object":
            return self.id
        if not key in self.meta :
            if self.get_asset():
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
        if not self.asset:
            if self.meta.get("id_asset", 0):
                self.asset = Asset(self["id_asset"], db = self.db)
            else:
                return False
        return self.asset

    def get_duration(self):
        if not self.id_asset: 
            return self.mark_out() - self.mark_in()
        dur = self.get_asset()["duration"]
        if not dur:
            return 0
        mark_in  = self.mark_in()
        mark_out = self.mark_out()
        if mark_out > 0: dur -= dur - mark_out
        if mark_in  > 0: dur -= mark_in
        return dur



class Bin(NXObject):
    object_type = "bin"
    items = []

    def _new(self):
        self.meta = {}
        self.items = []

    def _load(self):
        if not self._load_from_cache():
            if not self.db:
                self.db = DB()
            db = self.db

            logging.debug("Loading {!r} from DB".format(self))

            qcols = ", ".join(self.ns_tags)
            db.query("SELECT {0} FROM nx_{1}s WHERE id_object={2}".format(qcols, self.object_type, self.id))
            try:
                result = db.fetchall()[0]
            except:
                logging.error("Unable to load {!r}".format(self))
                return False

            for tag, value in zip(self.ns_tags, result):
                self[tag] = value

            db.query("SELECT tag, value FROM nx_meta WHERE id_object = %s and object_type = %s", (self["id_object"], self.id_object_type()))
            for tag, value in db.fetchall():
                self[tag] = value

            db.query("SELECT id_object FROM nx_items WHERE id_bin = %s ORDER BY position", [self["id_object"]])
            self.items = []
            for id_item, in db.fetchall():
                self.items.append(Item(id_item, db=db))

            self._save_to_cache()
        return True


    def _load_from_cache(self):
        try:
            self.meta, itemdata = json.loads(cache.load("%s%d" % (self.ns_prefix, self.id)))
        except:
            return False
        self.items = []
        for idata in itemdata:
            self.items.append(Item(from_data=idata))
        return True

    def _save_to_cache(self):
        return cache.save("%s%d" % (self.ns_prefix, self["id_object"]), json.dumps([self.meta, [i.meta for i in self.items]]))

    def get_duration(self):
        dur = 0
        for item in self.items:
            dur += item.get_duration()
        return dur

    def delete_childs(self):
        for item in self.items:
            if item.id > 0:
                item.delete()


class Event(NXObject):
    object_type = "event"
    bin        = False
    asset      = False

    def _new(self):
        self["start"]      = 0
        self["stop"]       = 0
        self["id_channel"] = 0
        self["id_magic"]   = 0

    def get_bin(self):
        if not self.bin:
            self.bin = Bin(self["id_magic"])
        return self.bin

    def get_asset(self):
        if not self.asset:
            self.asset = Asset(self["id_magic"])
        return self.asset

        


def get_day_events(id_channel, date):
    day_start = datestr2ts(date)
    day_end   = datestr2ts(date, 23, 59, 59)
    db = DB()
    db.query("SELECT id_object FROM nx_events WHERE id_channel=%s AND start > %s AND start < %s ", (id_channel, day_start, day_end))
    for id_event, in db.fetchall():
        yield Event(id_event)


def get_bin_first_item(id_bin, db=False):
    if not db:
        db = DB()
    db.query("SELECT id_item FROM nx_items WHERE id_bin=%d ORDER BY position LIMIT 1" % id_bin)
    try:
        return db.fetchall()[0][0]
    except:
        return False


def get_next_item(id_item, db=False):
    if not id_item:
        return False
    logging.debug("Looking for item following item ID {}".format(id_item))


    current_item = Item(id_item, db=db)
    current_bin = Bin(current_item["id_bin"])
    try:
        return current_bin.items[current_item["position"]]
    except:
        #if not db:
        #    db = DB()
        #   find next bin, open bin, return first item if exist
        return current_bin.items[0]


