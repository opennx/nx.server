import os
import time
import copy

try:
    import yaml
except ImportError:
    yaml = False

from .core import *
from .core.base_objects import *
from .connection import *


__all__ = ["Asset", "Item", "Bin", "Event", "User", "anonymous"]


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


class ServerObject(BaseObject):
    def __init__(self, id=False, **kwargs):
        self._db = kwargs.get("db", False)
        self._cache = kwargs.get("cache", False)
        self.ns_prefix = self.object_type[0]
        super(ServerObject, self).__init__(id, **kwargs)

    @property
    def db(self):
        if not self._db:
            self._db = DB()
        return self._db

    @property
    def cache(self):
        return self._cache or cache

    def load(self, id):
        id = int(id)
        try:
            cache_key = "{0}{1}".format(self.ns_prefix, id)
            self.meta = json.loads(self.cache.load(cache_key))
        except Exception:
            logging.debug("Loading {} id {} from DB".format(self.object_type, id))
            id_object_type = OBJECT_TYPES[self.object_type]
            qcols = ", ".join(self.ns_tags + ["meta"])
            self.db.query("SELECT {} FROM nx_{}s WHERE id_object={}".format(qcols, self.object_type, id))
            try:
                result = self.db.fetchall()[0]
            except Exception:
                logging.error("Unable to load {!r}".format(self))
                return False

            meta = result[-1]
            if meta:
                for key in meta:
                    self.meta[key] = meta[key]
                self._save_to_cache()
                return True

            result = result[:-1]
            for tag, value in zip(self.ns_tags, result):
                self[tag] = value

            self.db.query("SELECT tag, value FROM nx_meta WHERE id_object = %s and object_type = %s", (id, id_object_type))
            for tag, value in self.db.fetchall():
                self[tag] = value
            self.meta["id"] = self.meta["id_object"] = id
            self.save(set_mtime=False)
        return True

    def _save_to_cache(self):
        return self.cache.save("{0}{1}".format(self.ns_prefix, self.id), json.dumps(self.meta))

    def save(self, **kwargs):
        super(ServerObject, self).save(**kwargs)
        id_object_type = OBJECT_TYPES[self.object_type]

        created = False
        ns_tags = copy.copy(self.ns_tags)
        jsonb = config.get("jsonb", False)
        if jsonb:
            ns_tags.extend(["meta", "ft_index"])

        if self.id:
            q = "UPDATE nx_{}s SET {} WHERE id_object = {}".format(
                    self.object_type,
                    ", ".join("{}=%s".format(tag) for tag in ns_tags if tag != "id_object"),
                    self.id
                )
            v = [self[tag] for tag in self.ns_tags if tag != "id_object"]
            if jsonb:
                v.extend([json.dumps(self.meta), create_ft_index(self.meta)])

            self.db.query(q, v)
            self.db.query("DELETE FROM nx_meta WHERE id_object = {0} and object_type = {1}".format(self.id, id_object_type))
        else:
            self["ctime"] = self["ctime"] or time.time()
            created = True
            q = "INSERT INTO nx_{0}s ({1}) VALUES ({2})".format(
                    self.object_type,
                    ", ".join(tag for tag in ns_tags if tag != 'id_object'),
                    ", ".join(["%s"]*(len(ns_tags)-1))
                )
            v = [self[tag] for tag in self.ns_tags if tag != "id_object"]
            if jsonb:
                v.extend([json.dumps(self.meta), create_ft_index(self.meta)])

            self.db.query(q, v)
            self.meta["id_object"] = self.meta["id"] = self.db.lastid() #TODO: id_object is deprecated
            self.db.query("UPDATE nx_{}s SET meta=%s WHERE id_object=%s".format(self.object_type), [json.dumps(self.meta), self.id])
            logging.info("{!r} created".format(self))

        for tag in self.meta:
            if tag in self.ns_tags:
                continue
            value = meta_types.unformat(tag, self.meta[tag])
            q = "INSERT INTO nx_meta (id_object, object_type, tag, value) VALUES (%s, %s, %s, %s)"
            v = [self.id, id_object_type, tag, value]
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
        #super(ServerObject, self).save(self) #WHY????
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
    ns_tags = ["id_object", "media_type", "content_type", "id_folder", "origin", "version_of", "status", "ctime", "mtime"]

    def load_sidecar_metadata(self):
        path_elms = os.path.splitext(self.file_path)[0].split("/")[1:]
        for i in range(len(path_elms)):

            nxmeta_name = "/" + reduce(os.path.join, path_elms[:i]+["{}.json".format(path_elms[i])])
            if os.path.exists(nxmeta_name):
                try:
                    self.meta.update(json.loads(open(nxmeta_name).read()))
                except Exception:
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
                except Exception:
                    logging.warning("Unable to parse {}".format(nxmeta_name))
                else:
                    logging.debug("Applied meta from template {}".format(nxmeta_name))




class Item(ItemMixIn, ServerObject):
    ns_tags = ["id_object", "id_asset", "id_bin", "position", "ctime", "mtime"]

    def __getitem__(self, key):
        if key == "id_asset":
            return int(self.meta.get("id_asset", 0))
        return super(ServerObject, self).__getitem__(key)

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
    ns_tags = ["id_object", "bin_type", "ctime", "mtime"]
    def load(self, id):
        super(ServerObject, self).load(id)
        if hasattr(self, "items"):
            return True
        self.items = []
        db = self._db
        db.query("SELECT i.meta, a.meta FROM nx_items AS i, nx_assets AS a WHERE i.id_object = %s AND i.id_asset = a.id_object", [id])
        for imeta, ameta in db.fetchall():
            item = Item(meta=imeta, db=db)
            item._asset = Asset(meta=ameta, db=db)
            self.items.append(item)

    def _load_from_cache(self, id):
        try:
            self.meta, itemdata = json.loads(self.cache.load("{}{}".format(self.ns_prefix, id)))
        except Exception:
            return False
        self.items = []
        for idata in itemdata:
            self.items.append(Item(meta=idata, db=self._db))
        return True

    def _save_to_cache(self):
        assert type(self.id) == int
        key = "{}{}".format(self.ns_prefix, self.id)
        data = json.dumps([self.meta, [i.meta for i in self.items]])
        return self.cache.save(key, data)

    def delete_childs(self):
        for item in self.items:
            if item.id > 0:
                item.delete()
        return True


class Event(EventMixIn, ServerObject):
    ns_tags = ["id_object", "start", "stop", "id_channel", "id_magic", "ctime", "mtime"]

    @property
    def bin(self):
        if not hasattr(self, "_bin") or not self._bin:
            self._bin = Bin(self["id_magic"], db=self._db, cache=self.cache)
        return self._bin

    @property
    def asset(self):
        if not hasattr(self, "_asset") or not self._asset:
            self._asset = Asset(self["id_magic"], db=self._db, cache=self.cache)
        return self._asset


class User(UserMixIn, ServerObject):
    ns_tags = ["id_object", "login", "password", "ctime", "mtime"]

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
            return meta_types[key].default
        return self.meta[key]


anonymous = User(meta={
        "login" : "Anonymous"
    })
