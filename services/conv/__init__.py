#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *
from nx.jobs import Job
from nx.assets import *
from nx.common.metadata import meta_types
from nx.common.filetypes import file_types


from encoders import FFMPEG


encoders = {
    "ffmpeg" : FFMPEG
}



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
                if eval(svc_cond): 
                    match = True

            if not match:
                continue

            logging.debug("Registering action {}".format(title))
            self.allowed_actions[id_action] = config


    def on_main(self):
        job = Job(self.id_service, self.allowed_actions.keys())
        if not job:
            return

        id_asset = job.id_object
        asset = Asset(id_asset)

        try:
            vars = json.loads(job.settings)
        except:
            vars = {}

        action_config = self.allowed_actions[job.id_action]
        tasks = action_config.findall("task")

        for id_task, task in enumerate(tasks):
            try:
                using = task.attrib["using"]
            except:
                continue

            if not using in encoders:
                continue

            logging.info("Configuring task {} of {}".format(id_task+1, len(tasks)) )
            encoder = encoders[using](asset, task, vars)
            err = encoder.configure()

            if err:
                job.fail(err)
                return

            logging.info("Starting task {} of {}".format(id_task+1, len(tasks)) )
            encoder.run()

            while encoder.is_working():
                time.sleep(.1)

            if encoder.get_progress() == FAILED:
                job.fail()
                return

            logging.info("Finalizing task {} of {}".format(id_task+1, len(tasks)) )
            err = encoder.finalize()
            if err:
                job.fail(err)
                return

            vars = encoder.vars


        job.done()


