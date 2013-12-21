#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import *

__all__ = ["meta_types", "Asset", "asset_by_path", "asset_by_full_path", "meta_exists", "browse"]

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


class MetaTypes(dict):
    def __init__(self):
        super(MetaTypes, self).__init__()
        self._load()

    def _load(self):
        db = DB()
        db.query("SELECT namespace, tag, editable, searchable, class, default_value,  settings FROM nx_meta_types")
        for ns, tag, editable, searchable, class_, default, settings in db.fetchall():
            meta_type = MetaType(tag)
            meta_type.namespace  = ns
            meta_type.editable   = bool(editable)
            meta_type.searchable = bool(searchable)
            meta_type.class_     = class_
            meta_type.default    = default
            meta_type.settings   = settings
            db.query("SELECT lang, alias FROM nx_meta_aliases WHERE tag='%s'" % tag)
            for lang, alias in db.fetchall():
                meta_type.aliases[lang] = alias
            self[tag] = meta_type

    def _default(self):
        meta_type = MetaType("Unknown")
        meta_type.namespace  = "site"
        meta_type.editable   = 0
        meta_type.searchable = 0
        meta_type.class_     = TEXT
        meta_type.default    = ""
        meta_type.settings   = False
        return meta_type

    def __getitem__(self, key):
        return self.get(key, self._default())

    def format_default(self, key):
        if not key in self:
            return False
        else:
            return self.format(key, self[key].default)

    def col_alias(self, key, lang):
        if not key in self: 
            return self[key].aliases.get(lang,key)

    def format(self, key, value):
        if not key in self:
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

    def read_format(self, key, value):
        """ Human readable representation. Value must be formated first using format"""
        if not key in self:
            return value
        mtype = self[key]

        if   mtype.class_ in [TEXT, BLOB]:         return value
        elif mtype.class_ in [INTEGER, NUMERIC]:   return ["%.3f","%d"][float(value).is_integer()] % value
        elif mtype.class_ == DATE:                 return strftime("%Y-%m-%d",localtime(value))
        elif mtype.class_ == TIME:                 return strftime("%H:%M",localtime(value))
        elif mtype.class_ == DATETIME:             return strftime("%Y-%m-%d %H:%M",localtime(value))
        elif mtype.class_ == FILESIZE:
            for x in ['bytes','KB','MB','GB','TB']:
                if value < 1024.0: return "%3.1f %s" % (value, x)
                value /= 1024.0
        else: return value



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
            "ctime"        : time(), 
            "mtime"        : time(), 
            "origin"      : "Library", 
            "version_of"   : 0, 
            "status"       : OFFLINE
        }

    def _save(self):
        pass

    def save(self, set_mtime=True):
        if set_mtime:
            self["mtime"] = time()
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


class Asset(AssetPrototype):
    """ Server variant of Asset class"""
    def _load(self,id_asset):
        if not self.db:
            self.db = DB()
        db = self.db

        self.meta = {}

        db.query("SELECT media_type, content_type, id_folder, ctime, mtime, origin, version_of, status FROM nx_assets WHERE id_asset = %d" % self.id_asset)
        try:
            self["media_type"], self["content_type"], self["id_folder"], self["ctime"], self["mtime"], self["origin"], self["version_of"], self["status"] = db.fetchall()[0]
        except:
            logging.error("Unable to load Asset ID %d" % id_asset)
            return False

        self["id_asset"] = self.id_asset = id_asset
        db.query("SELECT tag, value FROM nx_meta WHERE id_asset = %d" % id_asset)
        for tag, value in db.fetchall():
            self[tag] = value

    def _save_to_cache(self):
        return cache.save("A%d"%self.id_asset, json.dumps(self.meta))

    def _save(self):
        if not self.db:
            self.db = DB()
        db = self.db

        if self.id_asset:
            query = "UPDATE nx_assets SET media_type=%d, content_type=%d, id_folder=%d, ctime=%d, mtime=%d, origin='%s', version_of=%d, status=%d WHERE id_asset=%d" % \
                                        (self["media_type"], self["content_type"], self["id_folder"], self["ctime"], self["mtime"], self["origin"], self["version_of"], self["status"],   self.id_asset)
            db.query(query)
        else:
            query = "INSERT INTO nx_assets (media_type,content_type,id_folder, ctime, mtime, origin, version_of, status) VALUES (%d, %d, %d, %d, %d, '%s', %d, %d)" % \
                                        (self["media_type"], self["content_type"], self["id_folder"], self["ctime"], self["mtime"], self["origin"], self["version_of"], self["status"])
            db.query(query)
            self.id_asset = db.lastid()

        db.query("DELETE FROM nx_meta WHERE id_asset = %d" % self.id_asset)
        for tag in self.meta:
            if meta_types[tag].namespace == "a":
                continue
            value = self.meta[tag]
            query = "INSERT INTO nx_meta (id_asset,tag,value) VALUES (%d, '%s', '%s')"% (self.id_asset, tag, db.sanit(value))
            db.query(query)

        if self._save_to_cache():
            db.commit()
            return True
        else:
            db.rollback()
            return False


#################################################
## Miscelaneous asset related utilities



def asset_by_path(id_storage, path, db=False):
    if not db: db = DB()
    db.query("""SELECT id_asset FROM nx_meta 
                WHERE tag='id_storage' 
                AND value='%s' 
                AND id_asset IN (SELECT id_asset FROM nx_meta WHERE tag='path' and value='%s')
                """ % (id_storage, db.sanit(path.replace("\\","/"))))
    try:
        return db.fetchall()[0][0]
    except: 
        return False


def asset_by_full_path(path, db=False):
    for s in storages:
        if path.startswith(storages[s].get_path()):
            return asset_by_path(s,path.lstrip(s.path),db=db)
    return False


def meta_exists(tag, value, db=False):
    if not db: db = DB()
    db.query("""SELECT a.id_asset FROM nx_meta as m, nx_assets as a 
                WHERE a.status <> 'TRASHED' 
                AND a.id_asset = m.id_asset 
                AND m.tag='%s' 
                AND m.value='%s'
                """ % (tag, value))
    try:
        return res[0][0]
    except:
        return False

def browse(query={}):
    if "fulltext" in query:
        pass