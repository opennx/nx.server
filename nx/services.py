#!/usr/bin/env python
# -*- coding: utf-8 -*-

from server import *

class ServicePrototype(object):
    def __init__(self, id_service, settings=False):
        logging.info("Initialising service")
        self.id_service = id_service
        self.settings   = settings

        try:
            self.onInit()
        except:
            logging.error("Unable to initialize service. %s" % str(sys.exc_info()))
            self.shutdown()
        else:
            db = DB()
            db.query("UPDATE nx_services SET last_seen = %d, state=1 WHERE id_service=%d" % (time.time(), self.id_service))
            db.commit()
        logging.goodnews("Service started")

    def onInit(self):
        pass

    def onMain(self):
        pass        

    def soft_stop(self):
        db = DB()
        db.query("UPDATE nx_services SET state=3 WHERE id_service=%d"%self.id_service)
        db.commit()

    def shutdown(self):
        #db = DB()
        #db.query("UPDATE nx_services SET autostart=0 WHERE id_service=%d" % self.id_service)
        #db.commit()
        sys.exit(-1)

    def heartbeat(self):
        db = DB()
        db.query("SELECT state FROM nx_services WHERE id_service=%s" % self.id_service)
        try:
            state = db.fetchall()[0][0]
        except:
            state = KILL
        else:
            db.query("UPDATE nx_services SET last_seen = %d, state=1 WHERE id_service=%d" % (time.time(), self.id_service))

        if state in [STOPPED, STOPPING, KILL]:
            logging.info("Shutting down")
            sys.exit(1)

__all__ = ["ServicePrototype"]