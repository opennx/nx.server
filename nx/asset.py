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


class MetaDict(dict):
    def __init__(self):
        super(Config, self).__init__()
        self._load()

    def _load(self):
        #TODO: This should be loaded from database
        from default import BASE_META_SET
        for ns, tag, editable, searchable, class_, config in BASE_META_SET:
            meta_type = MetaType()
            meta_type.editable   = bool(editable)
            meta_type.searchable = bool(searchable)
            meta_type.class_     = class_
            meta_type.config     = config
            self[tag] = meta_type


meta_types = MetaDict()



class AssetPrototype(object):
    """This prototype can be used both on client and server"""

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
            self._new(self)

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


    def __setitem__(self,key,value):
        key   = key.lower().strip()
        value = value.strip()
        if not value:
            del self[key]
            return True


    def __delitem__(self,key):
        key = key.lower().strip()



class Asset(AssetPrototype):
    """ Server variant of Asset class"""
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