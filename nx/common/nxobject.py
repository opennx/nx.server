#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx.common import *
from nx.connection import *
from nx.common.metadata import MetaType, meta_types

__all__ = ["NXObject"]

class NXBaseObject(object):
    object_type = "asset"

    def __init__(self, id_object=False, db=False, from_data=False):
        self.ns_prefix = self.object_type[0]
        self.ns_tags   = meta_types.ns_tags(self.ns_prefix)
        self.id = id_object
        self.meta = {}

        if from_data:
            self.meta = from_data
        else:
            self.db = db
            if self.id:
                self._load()
            else:
                self._new()

    def id_object_type(self):
        return OBJECT_TYPES[self.object_type]

    def _new(self):
        self.meta = {}

    def _load(self):
        pass

    def _save(self):
        pass
  
    def save(self, set_mtime=True):
        if set_mtime:
            self["mtime"] = time.time()
        self._save()

    def __getitem__(self, key):
        key = key.lower().strip()
        if not key in self.meta:
            return meta_types.format_default(key)
        return self.meta[key]

    def __setitem__(self, key, value):
        key = key.lower().strip()
        if not value:
            del self[key]
            return True
        self.meta[key] = meta_types.format(key,value)

    def __delitem__(self, key):
        key = key.lower().strip()
        if key in meta_types and meta_types[key].namespace == self.object_type[0]: 
            return
        if not key in self.meta:
            return
        del self.meta[key]

    def __repr__(self):
        try:
            title = self.meta.get("title","")
            if title: 
                title = " (%s)" % title
            return "%s ID:%d%s" % (self.object_type, self.id, title)
        except:
            return "%s ID:%d" % (self.object_type, self.id)





class NXServerObject(NXBaseObject):
    def _load(self):
        try:
            self.meta = json.loads(cache.load("%s%d" % (self.ns_prefix, self.id)))
            if not self.meta:
                raise Exception
        except:
            if not self.db:
                self.db = DB()
            db = self.db

            logging.debug("Loading %s from DB" % self)

            qcols = ", ".join(self.ns_tags)
            db.query("SELECT %s FROM nx_%ss WHERE id_object = %d" % (qcols, self.object_type, self.id))
            try:
                result = db.fetchall()[0]
            except:
                logging.error("Unable to load %s" % self)
                return False

            for tag, value in zip(self.ns_tags, result):
                self[tag] = value

            db.query("SELECT tag, value FROM nx_meta WHERE id_object = %s and object_type = %s", (self["id_object"], self.id_object_type()))
            for tag, value in db.fetchall():
                self[tag] = value

            self._save_to_cache()

    def _save_to_cache(self):
        return cache.save("%s%d" % (self.ns_prefix, self["id_object"]), json.dumps(self.meta))

    def _save(self):
        if not self.db:
            self.db = DB()
        db = self.db
     
        if self["id_object"]:
            q = "UPDATE nx_%ss SET %s WHERE id_object = %d" % (self.object_type,
                                                               ", ".join("%s = %%s" % tag for tag in self.ns_tags if tag != "id_object"),
                                                               self["id_object"]
                                                               )
            v = [self[tag] for tag in self.ns_tags if tag != "id_object"]
            db.query(q, v)
        else:
            self["ctime"] = time.time()
            q = "INSERT INTO nx_%ss (%s) VALUES (%s)" % ( self.object_type,  
                                                          ", ".join(tag for tag in self.ns_tags if tag != 'id_object'),
                                                          ", ".join(["%s"]*(len(self.ns_tags)-1)) 
                                                        )
            v = [self[tag] for tag in self.ns_tags if tag != "id_object"]
            db.query(q, v)
            self["id_object"] = db.lastid()

        db.query("DELETE FROM nx_meta WHERE id_object = %d and object_type = %d" % (self["id_object"], self.id_object_type()))
        for tag in self.meta:
            if tag in self.ns_tags:
                continue
            value = self.meta[tag]
            q = "INSERT INTO nx_meta (id_object, object_type, tag, value) VALUES (%s, %s, %s, %s)"
            v = [self["id_object"], self.id_object_type(), tag, value]
            db.query(q, v)

        if self._save_to_cache():
            db.commit()
            return True
        else:
            db.rollback()



class NXClientObject(NXBaseObject):
    def _load(self):
        pass
    # TODO: hive loading, save, ....



if connection_type == "server":
    NXObject = NXServerObject
else:
    NXObject = NXClientObject




class AssetBase(object):
    object_type = "asset"

    def _new(self):
        self.meta = {
        
        }

    def mark_in(self, new_val=False):
        if new_val:
            self["mark_in"] = new_val
        return self["mark_in"]

    def mark_out(self, new_val=False):
        if new_val:
            self["mark_out"] = new_val
        return self["mark_out"]
        
    def get_file_path(self):
        return os.path.join(storages[self["id_storage"]].get_path(), self["path"])

    def get_duration(self):
        dur = float(self.meta.get("duration",0))
        mki = float(self.meta.get("mark_in" ,0))
        mko = float(self.meta.get("mark_out",0))
        if not dur: return 0
        if mko > 0: dur -= dur - mko
        if mki > 0: dur -= mki
        return dur
