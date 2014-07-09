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
        if not self["id_asset"]: 
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

    def delete_childs(self, db):
        for item in self.items:
            if item.id > 0:
                item.db = db
                item.delete()
        return True


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
        if not self.db:
            self.db = DB()
        db = self.db
        if not self.bin:
            self.bin = Bin(self["id_magic"], db=db)
        return self.bin

    def get_asset(self):
        if not self.db:
            self.db = DB()
        db = self.db
        if not self.asset:
            self.asset = Asset(self["id_magic"], db=db)
        return self.asset


def bin_refresh(bins, sender=False, db=False):
    if not db:
        db = DB()
    for id_bin in bins:
        cache.delete("b{}".format(id_bin))
    bq = ", ".join([str(b) for b in bins])
    changed_rundowns = []
    db.query("SELECT e.id_channel, e.start FROM nx_events as e, nx_channels as c WHERE c.channel_type = 0 AND c.id_channel = e.id_channel AND id_magic in ({})".format(bq))
    for id_channel, start_time in db.fetchall():
        start_time = time.strftime("%Y-%m-%d", time.localtime(start_time))
        chg = [id_channel, start_time]
        if not chg in changed_rundowns:
            changed_rundowns.append(chg)
    if changed_rundowns:
        messaging.send("rundown_change", sender=sender, rundowns=changed_rundowns)
    return 202, "OK"

        
def get_day_events(id_channel, date, num_days=1):
    start_time = datestr2ts(date, *config["playout_channels"][id_channel].get("day_start", [6,0]))
    end_time   = start_time + (3600*24*num_days)
    db = DB()
    db.query("SELECT id_object FROM nx_events WHERE id_channel=%s AND start > %s AND start < %s ", (id_channel, start_time, end_time))
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

def get_item_event(id_item, db=False):
    if not db:
        db = DB
    db.query("""SELECT e.id_object from nx_items as i, nx_events as e where e.id_magic = i.id_bin and i.id_object = {} and e.id_channel in ({})""".format(
        id_item,
        ", ".join([str(f) for f in config["playout_channels"].keys()]) 
        ))
    try:
        return Event(db.fetchall()[0][0], db=db)
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
        if not db:
            db = DB()
        current_event = get_item_event(id_item, db=db)
        q = "SELECT id_object FROM nx_events WHERE id_channel = {} and start > {} ORDER BY start ASC LIMIT 1".format(current_event["id_channel"], current_event["start"])
        db.query(q)
        try:
            next_event = Event(db.fetchall()[0][0], db=db)
            next_bin = next_event.get_bin()
            if not next_bin.items:
                raise Exception
            return next_bin.items[0]
        except:
            logging.warning("There is no non-empty after this one. Looping current")
            return current_bin.items[0]


def get_item_runs(id_channel, from_ts, to_ts, db=False):
    db = db or DB()
    db.query("SELECT id_item, start, stop FROM nx_asrun WHERE start >= %s and start < %s ORDER BY start ASC", [int(from_ts), int(to_ts)] )
    result = {}
    for id_item, start, stop in db.fetchall():
        result[id_item] = (start, stop)
    return result