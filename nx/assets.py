#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import *

#
# Asset is ... 
#
#

class MetaType(object):
    editable   = False
    searchable = False
    class_     = TEXT
    config     = False

class MetaTypes(dict):
    def __init__(self):
        super(MetaTypes, self).__init__()
        self._load()

    def _load(self):
        #TODO: This should be loaded from database
        from default import BASE_META_SET
        for ns, tag, editable, searchable, class_, config in BASE_META_SET:
            meta_type = MetaType()
            meta_type.namespace  = ns
            meta_type.editable   = bool(editable)
            meta_type.searchable = bool(searchable)
            meta_type.class_     = class_
            meta_type.config     = config
            self[tag] = meta_type

    def format(self, tag, value):
        if not tag in self.meta_types:
            return value
        mtype = meta_types["tag"]

        ## PLEASE REFACTOR ME.
        if   mtype.class_ == TEXT:     return value
        elif mtype.class_ == INTEGER:  return int(value)
        elif mtype.class_ == NUMERIC:  return float(value)
        elif mtype.class_ == BLOB:     return value
        elif mtype.class_ == DATE:     return float(value)
        elif mtype.class_ == TIME:     return float(value)
        elif mtype.class_ == DATETIME: return float(value)
        elif mtype.class_ == TIMECODE: return float(value)
        elif mtype.class_ == DURATION: return float(value)
        elif mtype.class_ == REGION:   return json.loads(value)
        elif mtype.class_ == REGIONS:  return json.loads(value)
        elif mtype.class_ == SELECT:   return value
        elif mtype.class_ == ISELECT:  return int(value)
        elif mtype.class_ == COMBO:    return value
        elif mtype.class_ == FOLDER:   return int(value)
        elif mtype.class_ == STATUS:   return int(value)
        elif mtype.class_ == STATE:    return int(value)


meta_types = MetaTypes()



class AssetPrototype(object):
    def __init__(self,id_asset=False,db=False):
        self.id_asset = id_asset
        self.meta = {}
        if self.id_asset == -1: #id_asset==-1 is reserved for live events
            self["title/en-US"]  = "Live"
            self["title/cs-CZ"]  = "Živě"
            self["media_type"]   = VIRTUAL
            self["content_type"] = VIDEO
        elif self.id_asset:
            self._load(self.id_asset,db)
        else:
            self._new()

    def _load(self,id_asset,db=False):
        self.meta = {}

    def _new(self):
        self.meta = {}

    ## Asset loading/creating
    #######################################
    ## Special Getters

    def get_file_path(self):
        return False

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
            return False
        return self.meta[key]


    def __setitem__(self,key,value):
        key   = key.lower().strip()
        value = value.strip()
        if not value:
            del self[key]
            return True
        self.meta[key] = meta_types.format(key,value)


    def __delitem__(self,key):
        key = key.lower().strip()
        if key in meta_types and meta_types["key"].namespace == "a": 
            return
        if not key in self.meta:
            return
        del self.meta[key]



class Asset(AssetPrototype):
    """ Server variant of Asset class"""
    def _load(self,id_asset,db=False):
        pass

    def save(self):
        pass





#################################################
## Miscelaneous asset related utilities





def asset_by_path(storage, path):
    db.query("""SELECT id_asset FROM nx_meta 
                WHERE tag='STORAGE' 
                AND value='%s' 
                AND id_asset IN (SELECT id_asset FROM nx_meta WHERE tag='PATH' and value='%s')
                """ % (storage,path))
    try:
        return db.fetchall()[0][0]
    except: 
        return False

def asset_by_full_path(path):
    # for s in storages:
    #     if path.startswith(s.path):
    #         blah blah  TODO
    #         return asset_by_path(storage,path.lstrip(s.path))
    return False

def meta_exists(tag,value):
    db.query("""SELECT a.id_asset FROM nx_meta as m, nx_assets as a 
                WHERE a.status <> 'TRASHED' 
                AND a.id_asset = m.id_asset 
                AND m.tag='%s' 
                AND m.value='%s'
                """ % (tag,value))
    try:
        return res[0][0]
    except:
        return False