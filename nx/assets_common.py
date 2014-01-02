#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import *

class MetaType(object):
    def __init__(self, title):
        self.title      = title
        self.namespace  = "site"
        self.editable   = False
        self.searchable = False
        self.class_     = TEXT
        self.default    = False
        self.settings   = False
        self.aliases    = {}

    def alias(self, lang='en-US'):
        return self.aliases.get(lang, self.title)

    def pack(self):
        return {
                "title"      : self.title,
                "namespace"  : self.namespace,
                "editable"   : self.editable,
                "searchable" : self.searchable,
                "class"      : self.class_,
                "default"    : self.default,
                "settings"   : self.settings,
                "aliases"    : self.aliases
                }

class MetaTypes(dict):
    def __init__(self):
        super(MetaTypes, self).__init__()
        self._load()

    def __getitem__(self, key):
        return self.get(key, self._default())

    def _load(self):
        pass

    def _default(self):
        meta_type = MetaType("Unknown")
        meta_type.namespace  = "site"
        meta_type.editable   = 0
        meta_type.searchable = 0
        meta_type.class_     = TEXT
        meta_type.default    = ""
        meta_type.settings   = False
        return meta_type

    def format_default(self, key):
        if not key in self:
            return False
        else:
            return self.format(key, self[key].default)

    def col_alias(self, key, lang):
        if key in self: 
            return self[key].aliases.get(lang,key)
        return key

    def format(self, key, value):
        if not key in self:
            print "!!!!!! %s is not in metatypes" % key
            return value
        mtype = self[key]

        ## PLEASE REFACTOR ME.
        if  key == "path":                return value.replace("\\","/")

        elif mtype.class_ == TEXT:        return value.strip()
        elif mtype.class_ == INTEGER:     return int(value)
        elif mtype.class_ == NUMERIC:     return float(value)
        elif mtype.class_ == BLOB:        return value.strip()
        elif mtype.class_ == DATE:        return float(value)
        elif mtype.class_ == TIME:        return float(value)
        elif mtype.class_ == DATETIME:    return float(value)
        elif mtype.class_ == TIMECODE:    return float(value)
        elif mtype.class_ == DURATION:    return float(value)
        elif mtype.class_ == REGION:      return json.loads(value)
        elif mtype.class_ == REGIONS:     return json.loads(value)
        elif mtype.class_ == SELECT:      return value.strip()
        elif mtype.class_ == ISELECT:     return int(value)
        elif mtype.class_ == LIST:        return value.strip()
        elif mtype.class_ == COMBO:       return value.strip()
        elif mtype.class_ == FOLDER:      return int(value)
        elif mtype.class_ == STATUS:      return int(value)
        elif mtype.class_ == STATE:       return int(value)
        elif mtype.class_ == FILESIZE:    return int(value)
        elif mtype.class_ == MULTISELECT: return json.loads(value)
        elif mtype.class_ == PART:        return json.loads(value)
        elif mtype.class_ == BOOLEAN:     return int(value)
        elif mtype.class_ == STAR:        return int(value)

meta_types = MetaTypes()


class AssetPrototype(object):
    def __init__(self,id_asset=False,db=False):
        self.id_asset = id_asset
        self.db = db
        self.meta = {}
        if self.id_asset == -1: #id_asset==-1 is reserved for live events
            self["title"]  = "Live"
            self["media_type"]   = VIRTUAL
            self["content_type"] = VIDEO
        elif self.id_asset:
            self._load(self.id_asset)
        else:
            self._new()

    def _load(self,id_asset):
        self.meta = {}

    def _new(self):
        self.meta = {
            "id_asset"     : 0, 
            "media_type"   : VIRTUAL, 
            "content_type" : VIDEO, 
            "id_folder"    : 0, 
            "ctime"        : time.time(), 
            "mtime"        : time.time(), 
            "origin"      : "Library", 
            "version_of"   : 0, 
            "status"       : OFFLINE
        }

    def _save(self):
        pass

    def save(self, set_mtime=True):
        if set_mtime:
            self["mtime"] = time.time()
        self._save()

    ## Asset loading/creating
    #######################################
    ## Special Getters

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

    ## Special Getters
    #######################################
    ## Asset deletion

    def trash(self):
        pass

    def untrash(self):
        pass

    def purge(self):
        pass

    def make_offline(self):
        pass

    ## Asset deletion
    #######################################
    ## Getter / setter

    def __getitem__(self,key):
        key = key.lower().strip()
        if not key in self.meta:
            return meta_types.format_default(key)
        return self.meta[key]

    def __setitem__(self,key,value):
        key   = key.lower().strip()
        if not value:
            del self[key]
            return True
        self.meta[key] = meta_types.format(key,value)

    def __delitem__(self,key):
        key = key.lower().strip()
        if key in meta_types and meta_types[key].namespace == "a": 
            return
        if not key in self.meta:
            return
        del self.meta[key]

    def __repr__(self):
        try:
            title = self.meta.get("title","")
            if title: 
                title = " (%s)" % title
            return ("Asset ID:%d%s"%(self.id_asset,title))
        except:
            return("Asset ID:%d"%self.id_asset)
