from .common import *
from .constants import *
from .metadata import meta_types

__all__ = ["BaseObject", "BaseAsset", "BaseItem", "BaseBin", "BaseEvent", "BaseUser"]

class BaseObject(object):
    def __init__(self, id=False, **kwargs):
        self.id = id

        self.ns_prefix = self.object_type[0]
        self.ns_tags   = meta_types.ns_tags(self.ns_prefix)
        self.meta = {}

        self._loaded = False
        self._db = kwargs.get("db", False)
        self._cache = kwargs.get("cache", False)

        if "meta" in kwargs:
            assert hasattr(kwargs["meta"], "keys")
            self.meta = kwargs["meta"]
            self.id = self.meta.get("id_object", False)
            self._loaded = True
        else:
            if self.id:
                if self.load():
                    self._loaded = True
            else:
                self.new()
        self.meta["id"] = self.id # Nebula v.5 compatibility hack

    @property
    def object_type(self):
        return self.__class__.__name__.lower()

    def keys(self):
        return self.meta.keys()

    def id_object_type(self):
        return OBJECT_TYPES[self.object_type]

    def new(self):
        pass

    def load(self):
        pass

    def save(self, **kwargs):
        if kwargs.get("set_mtime", True):
            self["mtime"] = int(time.time())

    def delete(self, **kwargs):
        assert self.id > 0, "Unable to delete unsaved asset"

    def __getitem__(self, key):
        key = key.lower().strip()
        if not key in self.meta:
            return meta_types.format_default(key)
        return self.meta[key]

    def __setitem__(self, key, value):
        key = key.lower().strip()
        if value or type(value) in [float, int, bool]:
            self.meta[key] = meta_types.format(key,value)
        else:
            del self[key] # empty strings
        return True

    def __delitem__(self, key):
        key = key.lower().strip()
        if key in meta_types and meta_types[key].namespace == self.object_type[0]:
            return
        if not key in self.meta:
            return
        del self.meta[key]

    def __repr__(self):
        if self.id:
            result = "{} ID:{}".format(self.object_type, self.id)
        else:
            result = "new {}".format(self.object_type)
        title =  self.meta.get("title", "")
        if title:
            result += " ({})".format(title)
        return result

    def __len__(self):
        return self._loaded

    def show(self, key):
        return meta_types.humanize(key, self[key])







class BaseAsset(BaseObject):
    def mark_in(self, new_val=False):
        if new_val:
            self["mark_in"] = new_val
        return self["mark_in"]

    def mark_out(self, new_val=False):
        if new_val:
            self["mark_out"] = new_val
        return self["mark_out"]

    @property
    def file_path(self):
        try:
            return os.path.join(storages[self["id_storage"]].local_path, self["path"])
        except:
            return "" # Yes. empty string. keep it this way!!! (because of os.path.exists and so on)

    @property
    def duration(self):
        dur = float(self.meta.get("duration",0))
        mki = float(self.meta.get("mark_in" ,0))
        mko = float(self.meta.get("mark_out",0))
        if not dur: return 0
        if mko > 0: dur -= dur - mko
        if mki > 0: dur -= mki
        return dur



class BaseItem(BaseObject):
    _asset = False

    def new(self):
        super(BaseItem, self).new()
        self["id_bin"]    = False
        self["id_asset"]  = False
        self["position"]  = 0

    def __getitem__(self, key):
        key = key.lower().strip()
        if key == "id_object":
            return self.id
        if not key in self.meta :
            if self.asset:
                return self.asset[key]
            else:
                return False
        return self.meta[key]

    def mark_in(self, new_val=False):
        if new_val:
            self["mark_in"] = new_val
        return float(self["mark_in"])

    def mark_out(self, new_val=False):
        if new_val:
            self["mark_out"] = new_val
        return float(self["mark_out"])

    @property
    def asset(self):
        pass

    @property
    def bin(self):
        pass

    @property
    def event(self):
        pass

    @property
    def duration(self):
        """Final duration of the item"""
        if self["id_asset"]:
            dur = self.asset["duration"]
        elif self["duration"]:
            dur = self["duration"]
        else:
            return self.mark_out() - self.mark_in()
        if not dur:
            return 0
        mark_in  = self.mark_in()
        mark_out = self.mark_out()
        if mark_out > 0: dur -= dur - mark_out
        if mark_in  > 0: dur -= mark_in
        return dur


class BaseBin(BaseObject):
    def new(self):
        super(BaseBin, self).new()
        self.items = []


class BaseEvent(BaseObject):
    def new(self):
        super(BaseEvent, self).new()
        self["start"]      = 0
        self["stop"]       = 0
        self["id_channel"] = 0
        self["id_magic"]   = 0


class BaseUser(BaseObject):
    pass
