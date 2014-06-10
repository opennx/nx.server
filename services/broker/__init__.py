#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *
from nx.assets import Asset
from nx.jobs import send_to

class Service(ServicePrototype):
    def on_init(self):
        self.conditions = {}
        db = DB()
        db.query("SELECT id_action, title, config FROM nx_actions")
        for id_action, title, aconfig in db.fetchall():
            try:
                start_cond = ET.XML(aconfig).find("start_if").text
            except:
                logging.debug("No start condition for action {}".format(title))
                continue
            if start_cond:
                logging.debug("Initializing broker condition for {}".format(title))
                self.conditions[id_action] = (title, start_cond)


    def on_main(self):
        db = DB()
        db.query("SELECT id_object FROM nx_assets WHERE status = '{}'".format(ONLINE))
        for id_asset, in db.fetchall():
            self._proc(id_asset, db)


    def _proc(self, id_asset, db):
        asset = Asset(id_asset, db = db)
        for id_action in self.conditions:
            if "broker/started/{}".format(id_action) in asset.meta:
                continue
            cond_title, cond = self.conditions[id_action]
            if eval(cond):
                logging.info("{} matches action condition {}".format(asset, cond_title))
                res, msg = send_to(asset.id, id_action, settings={}, id_user=0, restart_existing=False, db=db)

                if success(res):
                    logging.info(msg)
                else:
                    logging.error(msg)
                
                asset["broker/started/{}".format(id_action)] = 1
                asset.save()


 