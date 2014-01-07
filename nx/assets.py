#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import *
from connection import *
from nxobject import NXObject


__all__ = ["Asset", "asset_by_path", "asset_by_full_path", "meta_exists"]



class NXAsset(object):
    object_type = "asset"

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





class Asset(NXObject, NXAsset):
    pass







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