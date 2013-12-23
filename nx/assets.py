#!/usr/bin/env python
# -*- coding: utf-8 -*-

from server import *
from assets_common import MetaType, Asset
from assets_common import meta_types

__all__ = ["meta_types", "AssetPrototype", "asset_by_path", "asset_by_full_path", "meta_exists", "browse"]


def load_meta_types():
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
        meta_types[tag] = meta_type

load_meta_types()



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
     try:
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
     except:
        print self.meta
        time.sleep(20)


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