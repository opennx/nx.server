#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import *
from connection import *
from metadata import MetaType, meta_types

__all__ = ["NXObject"]

class NXBaseObject(object):
    object_type = "asset"

    def __init__(self, id_object=False, db=False, from_data=False):
        self.ns_prefix = self.object_type[0]
        self.ns_tags   = meta_types.ns_tags(self.ns_prefix)

        if from_data:
            self.meta = from_data
        else:
            self.id_object = id_object
            self.db = db
            if self.id_object:
                self.load()
            else:
                self.new()

    def id_object_type(self):
        return OBJECT_TYPES[self.object_type]

    def new(self):
        self.meta = {}

    def load(self):
        self._load()

    def save(self, set_mtime=True):
        if set_mtime:
            self["mtime"] = time.time()
        self._save()

    def _save(self):
        pass

    def _load(self):
        pass

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
            return ("%s ID:%d%s" % (self.object_type, self["id_object"], title))
        except:
            return("%s ID:%d" % self["id_object"])





class NXServerObject(NXBaseObject):
    def _load(self):
        try:
            self.meta = json.loads(cache.load("%s%d" % (self.ns_prefix, self.id_object)))
        except:
            if not self.db:
                self.db = DB()
            db = self.db

            logging.debug("Loading %s from DB" % self)

            qcols = ", ".join(self.ns_tags)
            q = "SELECT %s FROM nx_%ss WHERE id_object = %d" % (qcols, self.object_type, self.id_object)
            try:
                result = db.fetchall()[0]
            except:
                logging.error("Unable to load %s" % self)
                return False

            for tag, value in zip(self.ns_tags, result):
                self[tag] = value

            db.query("SELECT tag, value FROM nx_meta WHERE id_object = %d and object_type = %d" % self["id_object"], self.id_object_type())
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
            pass
            #query = "UPDATE nx_assets SET media_type=%d, content_type=%d, id_folder=%d, ctime=%d, mtime=%d, origin='%s', version_of=%d, status=%d WHERE id_asset=%d" % \
            #                            (self["media_type"], self["content_type"], self["id_folder"], self["ctime"], self["mtime"], self["origin"], self["version_of"], self["status"],   self.id_asset)
            #db.query(query)
        else:
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
    pass





if connection_type == "server":
    NXObject = NXServerObject
else:
    NXObject = NXClientObject