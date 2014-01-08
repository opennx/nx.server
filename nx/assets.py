#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import *
from connection import *

from nxobject import NXObject, AssetBase
from metadata import meta_types


from utils import *

__all__ = ["Asset", "asset_by_path", "asset_by_full_path", "meta_exists"]

class Asset(NXObject, AssetBase):
    def trash(self):
        pass

    def untrash(self):
        pass

    def purge(self):
        pass

    def make_offline(self):
        pass





	## END OF ASSET CLASS
    #######################


def asset_by_path(id_storage, path, db=False):
    if not db: 
        db = DB()
    db.query("""SELECT id_object FROM nx_meta 
                WHERE object_type = 0 
                AND tag='id_storage' 
                AND value='%s' 
                AND id_object IN (SELECT id_object FROM nx_meta WHERE object_type = 0 AND tag='path' AND value='%s')
                """ % (id_storage, db.sanit(path.replace("\\","/"))))
    try:
        return db.fetchall()[0][0]
    except: 
        return False


def asset_by_full_path(path, db=False):
    if not db:
        db = DB()
    for s in storages:
        if path.startswith(storages[s].get_path()):
            return asset_by_path(s,path.lstrip(s.path),db=db)
    return False


def meta_exists(tag, value, db=False):
    if not db: 
        db = DB()
    db.query("""SELECT a.id_asset FROM nx_meta as m, nx_assets as a 
                WHERE a.status <> 'TRASHED' 
                AND a.id_asset = m.id_object
                AND m.object_type = 0
                AND m.tag='%s' 
                AND m.value='%s'
                """ % (tag, value))
    try:
        return res[0][0]
    except:
        return False