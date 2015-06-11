#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *
from nx.objects import Asset
from nx.shell import shell


class BaseAnalyzer():
    condition = False
    proc_name = "base"
    version   = 1.0

    def __init__(self, asset):
        self.asset = asset
        self.result = {}
        self.status = self.proc()

    def update(self, key, value):
        self.result[key] = value

    def proc(self):
        pass



class Analyzer_AV(BaseAnalyzer):
    condition = "not 'audio/r128/i' in asset.meta"
    proc_name = "av"
    version   = 1.0
    
    def proc(self):
        fname = self.asset.file_path
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
        return True


class Analyzer_BPM(BaseAnalyzer):
    condition = "asset['origin'] == 'Production' and asset['id_folder'] == 5  and not 'audio/bpm' in asset.meta"
    proc_name = "bpm"
    version   = 1.0

    def proc(self):
        fname = self.asset.file_path
        s = shell("ffmpeg -i \"{}\" -vn -ar 44100 -f f32le - 2> /dev/null | bpm".format(fname))
        try:
            bpm = float(s.stdout().read())
        except:
            return False 
        self.update("audio/bpm", bpm)
        return True




class Service(ServicePrototype):
    def on_init(self):
      self.max_mtime = 0
      self.analyzers = [
        Analyzer_AV,
        Analyzer_BPM
        ]

    def on_main(self):
        db = DB()
        db.query("SELECT id_object, mtime FROM nx_assets WHERE status = '{}' and mtime > {}".format(ONLINE, self.max_mtime))
        for id_asset, mtime in db.fetchall():
            self.max_mtime = max(self.max_mtime, mtime)
            self._proc(id_asset, db)

    def _proc(self, id_asset, db):
        asset = Asset(id_asset, db = db)
        for analyzer in self.analyzers:

            qinfo = asset["qc/analyses"] or {}
            if type(qinfo) == str:
                qinfo = json.loads(qinfo)

            if analyzer.procname in qinfo and (qinfo[analyzer.procname] == -1 or qinfo[analyzer.procname] >= analyzer.version ):
                continue

            if eval(analyzer.condition):
                a = analyzer(asset)

                ## Reload asset (it may be changed by someone during analysis
                del(asset)
                asset = Asset(id_asset, db=db)
                result = -1 if not a.status else analyzer.version

                qinfo = asset["qc/analyses"] or {}
                if type(qinfo) == str:
                    qinfo = json.loads(qinfo)
                qinfo[analyzer.procname] = result
                asset["qc/analyses"] = qinfo 

                ## Save result
                for key in a.result:
                    value = a.result[key]
                    if value:
                        logging.debug("Set {} {} to {}".format(asset, key, value))
                        asset[key] = value
                asset.save()
