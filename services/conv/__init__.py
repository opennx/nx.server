#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *
from nx.jobs import Job


class Encoder():
    def __init__(self, asset, task, vars):
        self.asset = asset
        self.task = task
        self.vars = vars

    def is_working(self):
        return False

    def get_message(self):
        return ""



class Service(ServicePrototype):
    def on_init(self):
        agent_type = "conv"
        id_service = self.id_service
        self.allowed_actions = {}
        db = DB()
        db.query("SELECT id_action, title, config FROM nx_actions ORDER BY id_action")
        for id_action, title, config in db.fetchall():
            try:
                config = ET.XML(config)
            except:
                logging.error("Unable to parse '{}' action configuration".format(title))
                continue

            try:
                svc_cond = config.find("on").text()
            except:
                match = True
            else:
                if not svc_cond:
                    continue

                match = False
                cmd = "if "+svc_cond+": match = True"
                exec (cmd)

            if not match:
                continue

            logging.debug("Registering action {}".format(title))
            self.allowed_actions[id_action] = config



    def on_main(self):
        job = Job(self.id_service, self.allowed_actions.keys())
        if not job:
            return

        id_asset = job.id_asset
        asset = Asset(id_asset)

        config = self.config
        vars = {}

        tasks = config.findall("tasks")

        for task in tasks:
            try:
                using = task.attrib["using"]
            except:
                continue

            if not using in encoders:
                continue

            encoder = encoders[using](asset, task, vars)
            while encoder.is_working():
                print (encoder.get_progress(), encoder.get_message() )
            
            vars = encoder.vars


