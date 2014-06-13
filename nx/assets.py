#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx.common import *
from nx.common.nxobject import NXObject, AssetBase
from nx.common.metadata import meta_types
from nx.common.utils import *

from connection import *


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


    def delete_childs(self, db):
        db = DB()
        db.query("SELECT id_object, id_bin FROM nx_items WHERE id_asset = {}".format(self.id))
        if db.fetchall():
            logging.warning("Unable to delete {}. Remove it from all bins first.".format(self))
            return False
        return True




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