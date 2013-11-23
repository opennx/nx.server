#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *

class Service(ServicePrototype):
    def onInit(self):
        self.message = "Hello world"

    def onMain(self):
        logging.info(self.message)