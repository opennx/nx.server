#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *
from nx.objects import Asset
from nx.shell import shell


class BaseAnalyzer():
    def __init__(self, asset):
        self.asset = asset
        self.result = {}
        self.proc()

    def update(self, key, value):
        self.result[key] = value

    def proc(self):
        pass



class Analyzer_AV(BaseAnalyzer):
    def proc(self):
        fname = self.asset.get_file_path()
        r128tags = [
                ("I:",         "audio/r128/i"),
                ("Threshold:", "audio/r128/t"),
                ("LRA:",       "audio/r128/lra"),
                ("Threshold:", "audio/r128/lra/t"),
                ("LRA low:",   "audio/r128/lra/l"),
                ("LRA high:",  "audio/r128/lra/r"),
            ]
        exp_r128tag = r128tags.pop(0) 
        s = shell("ffmpeg -i \"{}\" -vn -filter_complex ebur128 -f null -".format(fname))
        for line in s.stderr().readlines():
            line = line.strip()
            if line.startswith(exp_r128tag[0]):
                value = float(line.split()[-2])
                self.update(exp_r128tag[1], value)
                try:
                    exp_r128tag = r128tags.pop(0)
                except:
                    break

class Analyzer_BPM(BaseAnalyzer):
    def proc(self):
        fname = self.asset.get_file_path()        
        s = shell("ffmpeg -i \"{}\" -vn -ar 44100 -f f32le - 2> /dev/null | ./bpm".format(fname))
        try:
            bpm = float(s.stdout().read())
        except:
            bpm = 0
        self.update("audio/bpm", bpm)





class Service(ServicePrototype):
    def on_init(self):
      self.max_mtime = 0
      self.analyzers = [
        ("not 'audio/r128/i' in asset.meta", Analyzer_AV),
        ("asset['origin'] == 'Production' and asset['id_folder'] == 5  and not 'audio/bpm' in asset.meta", Analyzer_BPM)
        ]

    def on_main(self):
        db = DB()
        db.query("SELECT id_object, mtime FROM nx_assets WHERE status = '{}' and mtime > {}".format(ONLINE, self.max_mtime))
        for id_asset, mtime in db.fetchall():
            self.max_mtime = max(self.max_mtime, mtime)
            self._proc(id_asset, db)

    def _proc(self, id_asset, db):
        asset = Asset(id_asset, db = db)
        for condition, analyzer in self.analyzers:
            if eval(condition):
                a = analyzer(asset)
                for key in a.result:
                    value = a.result[key]
                    if value:
                        logging.debug("Set {} {} to {}".format(asset, key, value))
                        asset[key] = value
                if a.result:
                    asset.save()