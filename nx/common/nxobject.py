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
        self._loaded = False
        self.db = db

        if from_data:
            self.meta = from_data
            self.id = self.meta.get("id_object", False)
            self._loaded = True
        else:
            if self.id:
                if self._load():
                    self._loaded = True
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
        return self._save()

    def delete(self):
        pass

    def __getitem__(self, key):
        key = key.lower().strip()
        if not key in self.meta:
            return meta_types.format_default(key)
        return self.meta[key]

    def __setitem__(self, key, value):
        key = key.lower().strip()
        if value or type(key) in (float, int, bool):
            self.meta[key] = meta_types.format(key,value)
        else:
            del self[key]
        return True
        

    def __delitem__(self, key):
        key = key.lower().strip()
        if key in meta_types and meta_types[key].namespace == self.object_type[0]: 
            return
        if not key in self.meta:
            return
        del self.meta[key]

    def __repr__(self):
        try:
            title = self["title"]
            if title: 
                title = " ({})".format(title)
            return "{0} ID:{1}{2}".format(self.object_type, self.id, title)
        except:
            return "{0} ID:{1}".format(self.object_type, self.id)

    def __len__(self):
        return self._loaded




class NXServerObject(NXBaseObject):
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

            self._save_to_cache()
        return True

    def _load_from_cache(self):
        try:
            self.meta = json.loads(cache.load("{0}{1}".format(self.ns_prefix, self.id)))
        except:
            return False
        else:
            if self.meta:
                return True
            return False


    def _save_to_cache(self):
        return cache.save("{0}{1}".format(self.ns_prefix, self["id_object"]), json.dumps(self.meta))

    def _save(self):
        if not self.db:
            self.db = DB()
        db = self.db
     
        if self["id_object"]:
            q = "UPDATE nx_{0}s SET {1} WHERE id_object = {2}".format(self.object_type,
                                                                  ", ".join("{} = %s".format(tag) for tag in self.ns_tags if tag != "id_object"),
                                                                  self["id_object"]
                                                                  )
            v = [self[tag] for tag in self.ns_tags if tag != "id_object"]
            db.query(q, v)
        else:
            self["ctime"] = time.time()
            q = "INSERT INTO nx_{0}s ({1}) VALUES ({2})".format( self.object_type,  
                                                          ", ".join(tag for tag in self.ns_tags if tag != 'id_object'),
                                                          ", ".join(["%s"]*(len(self.ns_tags)-1)) 
                                                        )
            v = [self[tag] for tag in self.ns_tags if tag != "id_object"]
            db.query(q, v)
            self["id_object"] = self.id = db.lastid()


        db.query("DELETE FROM nx_meta WHERE id_object = {0} and object_type = {1}".format(self["id_object"], self.id_object_type()))
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
            logging.error("Save {!r} to cache failed".format(self))
            db.rollback()
            return False

    def delete_childs(self):
        pass

    def delete(self):
        logging.debug("Deleting {!r}".format(self))
        if not self.db:
            self.db = DB()
        self.delete_childs()
        db = self.db
        db.query("DELETE FROM nx_meta WHERE id_object = %s and object_type = %s", [self.id, self.id_object_type()] )
        db.query("DELETE FROM nx_{}s WHERE id_object = %s".format(self.object_type), [self.id])
        db.commit()
        cache.delete("{0}{1}".format(self.ns_prefix, self.id))

        


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
        try:
            return os.path.join(storages[self["id_storage"]].get_path(), self["path"])
        except:
            return ""

    def get_duration(self):
        dur = float(self.meta.get("duration",0))
        mki = float(self.meta.get("mark_in" ,0))
        mko = float(self.meta.get("mark_out",0))
        if not dur: return 0
        if mko > 0: dur -= dur - mko
        if mki > 0: dur -= mki
        return dur
