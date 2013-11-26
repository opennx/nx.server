#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *

class ServicePrototype(object):
    def __init__(self, id_service, settings=False):
        logging.info("Initialising service")
        self.id_service = id_service
        self.settings   = settings
        self.onInit()
        logging.goodnews("Service started")

    def onInit(self):
        pass

    def onMain(self):
        pass        