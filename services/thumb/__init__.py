#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *
from nx.assets import *


class create_video_thumbnail(source, target, resolution=(512,288)):
    w, h = resolution



class Service(ServicePrototype):
    def on_init(self):
        pass

    def on_main(self):
        db = DB()
        db.query("SELECT id_object FROM nx_assets WHERE media_type=0 AND id_object NOT IN (SELECT id_object FROM nx_meta WHERE object_type=0 AND tag='has_thumbnail')")
        for id_object, in db.fetchall():
            asset = Asset(id_object, db=DB)
            spath = asset.get_file_path()
            tpath = 