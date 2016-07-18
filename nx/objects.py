import os
import time
import copy

try:
    import yaml
except:
    yaml = False

from .core import *
from .core.base_objects import *
from .connection import *

def create_ft_index(meta):
    idx = set()
    for key in meta:
        if not key in meta_types:
            continue
        if not meta_types[key]["searchable"]:
            continue
        value = meta[key]
        if type(value) not in [str, unicode]:
            continue
        slug_set = slugify(meta[key], make_set=True, min_length=3)
        idx |= slug_set
    return " ".join(idx)


class ServerObject(object):
    def __init__(self):
        self.ns_prefix = self.object_type[0]
        self.ns_tags   = meta_types.ns_tags(self.ns_prefix)
        self._db = kwargs.get("db", False)
        self._cache = kwargs.get("cache", False)
        BaseObject.__init__(self, id, **kwargs)

    @property
    def db(self):
        if not self._db:
            logging.info("{} is opening DB connection".format(self))
            self._db = DB()
        return self._db

    @property
    def cache(self):
        return self._cache or cache

    def load(self):
        try:
            self.meta = json.loads(self.cache.load("{0}{1}".format(self.ns_prefix, self.id)))
        except:
            logging.debug("Loading {!r} from DB".format(self))
            id_object_type = OBJECT_TYPES[self.object_type]
            qcols = ", ".join(self.ns_tags)
            self.db.query("SELECT {0} FROM nx_{1}s WHERE id_object={2}".format(qcols, self.object_type, self.id))
            try:
                result = self.db.fetchall()[0]
            except:
                logging.error("Unable to load {!r}".format(self))
                return False

            for tag, value in zip(self.ns_tags, result):
                self[tag] = value

            self.db.query("SELECT tag, value FROM nx_meta WHERE id_object = %s and object_type = %s", (self["id_object"], id_object_type))
            for tag, value in self.db.fetchall():
                self[tag] = value

            self._save_to_cache()
        self.meta["id"] = self.meta["id_object"]
        return True

    def _save_to_cache(self):
        return self.cache.save("{0}{1}".format(self.ns_prefix, self["id_object"]), json.dumps(self.meta))

    def save(self, **kwargs):
        BaseObject.save(self, **kwargs)
        id_object_type = OBJECT_TYPES[self.object_type]

        created = False
        ns_tags = copy.copy(self.ns_tags)
        jsonb = config.get("jsonb", False)
        if jsonb:
            ns_tags.extend(["meta", "ft_index"])

        if self["id_object"]:
            q = "UPDATE nx_{0}s SET {1} WHERE id_object = {2}".format(self.object_type,
                                                                  ", ".join("{} = %s".format(tag) for tag in ns_tags if tag != "id_object"),
                                                                  self["id_object"]
                                                                  )
            v = [self[tag] for tag in self.ns_tags if tag != "id_object"]
            if jsonb:
                v.extend([json.dumps(self.meta), create_ft_index(self.meta)])

            self.db.query(q, v)
            self.db.query("DELETE FROM nx_meta WHERE id_object = {0} and object_type = {1}".format(self["id_object"], id_object_type))
        else:
            self["ctime"] = self["ctime"] or time.time()
            created = True
            q = "INSERT INTO nx_{0}s ({1}) VALUES ({2})".format( self.object_type,
                                                          ", ".join(tag for tag in ns_tags if tag != 'id_object'),
                                                          ", ".join(["%s"]*(len(ns_tags)-1))
                                                        )
            v = [self[tag] for tag in self.ns_tags if tag != "id_object"]
            if jsonb:
                v.extend([json.dumps(self.meta), create_ft_index(self.meta)])

            self.db.query(q, v)
            self["id_object"] = self["id"] = self.id = self.db.lastid()
            logging.info("{!r} created".format(self))

        for tag in self.meta:
            if tag in self.ns_tags:
                continue
            value = meta_types.unformat(tag, self.meta[tag])
            q = "INSERT INTO nx_meta (id_object, object_type, tag, value) VALUES (%s, %s, %s, %s)"
            v = [self["id_object"], id_object_type, tag, value]
            self.db.query(q, v)

        if self._save_to_cache():
            self.db.commit()
            if kwargs.get("notify", True) and not created:
                messaging.send("objects_changed", objects=[self.id], object_type=self.object_type, user=config["user"])
            return True
        else:
            logging.error("Save {!r} to cache failed".format(self))
            self.db.rollback()
            return False

    def delete_childs(self):
        return True

    def delete(self):
        BaseObject.save(self)
        id_object_type = OBJECT_TYPES[self.object_type]
        if self.delete_childs():
            self.db.query("DELETE FROM nx_meta WHERE id_object = %s and object_type = %s", [self.id, id_object_type] )
            self.db.query("DELETE FROM nx_{}s WHERE id_object = %s".format(self.object_type), [self.id])
            self.db.commit()
            self.cache.delete("{0}{1}".format(self.ns_prefix, self.id))
            logging.info("{!r} deleted.".format(self))
            return True
        return False








class Asset(AssetMixIn, ServerObject):
    def load_sidecar_metadata(self):
        path_elms = os.path.splitext(self.file_path)[0].split("/")[1:]
        for i in range(len(path_elms)):

            nxmeta_name = "/" + reduce(os.path.join, path_elms[:i]+["{}.json".format(path_elms[i])])
            if os.path.exists(nxmeta_name):
                try:
                    self.meta.update(json.loads(open(nxmeta_name).read()))
                except:
                    logging.warning("Unable to parse %s" % nxmeta_name)
                else:
                    logging.debug("Applied meta from template %s" % nxmeta_name)

            nxmeta_name = "/" + reduce(os.path.join, path_elms[:i]+["{}.yaml".format(path_elms[i])])
            if os.path.exists(nxmeta_name):
                if not yaml:
                    logging.warning("YAML sidecar file exists, but pyyaml is not installed")
                    continue
                try:
                    f = open(nxmeta_name)
                    m = yaml.safe_load(f)
                    f.close()
                    self.meta.update(m)
                except:
                    logging.warning("Unable to parse %s" % nxmeta_name)
                else:
                    logging.debug("Applied meta from template {}".format(nxmeta_name))




class Item(ItemMixIn, ServerObject):
    @property
    def asset(self):
        if not self._asset:
            if self.meta.get("id_asset", 0):
                self._asset = Asset(self["id_asset"], db=self._db, cache=self._cache)
            else:
                return False
        return self._asset

    @property
    def bin(self):
        if not hasattr(self, "_bin"):
            self._bin = Bin(self["id_bin"], db=self._db, cache=self._cache)
        return self._bin

    @property
    def event(self):
        id_bin = int(self["id_bin"])
        if not id_bin:
            return False
        db = self._db
        if not hasattr(self, "_event"):
            db.query("SELECT id_object FROM nx_events WHERE id_magic=%s", [id_bin])
            res = db.fetchall()
            if not res:
                self._event = False
            else:
                self._event = Event(res[0][0], db=self._db, cache=self._cache)
        return self._event




class Bin(BinMixIn, ServerObject):
    def load(self):
        if not self._load_from_cache():
            id_object_type = OBJECT_TYPES[self.object_type]
            logging.debug("Loading {!r} from DB".format(self))

            qcols = ", ".join(self.ns_tags)
            self.db.query("SELECT {0} FROM nx_{1}s WHERE id_object={2}".format(qcols, self.object_type, self.id))
            try:
                result = self.db.fetchall()[0]
            except:
                logging.error("Unable to load {!r}".format(self))
                return False

            for tag, value in zip(self.ns_tags, result):
                self[tag] = value

            self.db.query("SELECT tag, value FROM nx_meta WHERE id_object = %s and object_type = %s", (self["id_object"], id_object_type))
            for tag, value in self.db.fetchall():
                self[tag] = value

            self.db.query("SELECT id_object FROM nx_items WHERE id_bin = %s ORDER BY position", [self["id_object"]])
            self.items = []
            for id_item, in self.db.fetchall():
                self.items.append(Item(id_item, db=self._db))
            self._save_to_cache()
        return True


    def _load_from_cache(self):
        try:
            self.meta, itemdata = json.loads(self.cache.load("%s%d" % (self.ns_prefix, self.id)))
        except:
            return False
        self.items = []
        for idata in itemdata:
            self.items.append(Item(from_data=idata, db=self._db))
        return True

    def _save_to_cache(self):
        return self.cache.save("%s%d" % (self.ns_prefix, self["id_object"]), json.dumps([self.meta, [i.meta for i in self.items]]))

    def delete_childs(self):
        for item in self.items:
            if item.id > 0:
                item.delete()
        return True


class Event(EventMixIn, ServerObject):
    @property
    def bin(self):
        if not self._bin:
            self._bin = Bin(self["id_magic"], db=self._db, cache=self.cache)
        return self._bin

    @property
    def asset(self):
        if not self._asset:
            self._asset = Asset(self["id_magic"], db=self._db, cache=self.cache)
        return self._asset


class User(UserMixIn, ServerObject):
    def has_right(self, key, val=True):
        if self["is_admin"]:
            return True
        key = "can/{}".format(key)
        if not self[key]:
            return False
        return self[key] == True or (type(self[key]) == list and val in self[key])

    def __getitem__(self, key):
        if self.meta.get("is_admin", False) and key.startswith("can/"):
            return True
        key = key.lower().strip()
        if not key in self.meta:
            return meta_types.format_default(key)
        return self.meta[key]
