#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *

def file_exists(rname):
    if not os.path.exists(rname):
        raise Exception

def dir_exists(rname):
    #TODO
    return True

def is_installed(rname):
    #TODO
    return True


class Service(ServicePrototype):
    def on_init(self):

        try:     
            self.exec_require = self.settings.find("require").text
        except:  
            self.exec_require = ""

        try:     
            self.exec_init = self.settings.find("init").text
        except:  
            self.exec_init = ""

        try:
            self.exec_main = self.settings.find("main").text
        except:  
            self.exec_main = ""

        try:
            exec(self.exec_require)
        except:
            logging.error("Worker requirements check failed. Shutting down.")
            self.shutdown()
        exec (self.exec_init)

    def on_main(self):
        if self.exec_main:
            exec (self.exec_main)
        