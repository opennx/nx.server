#!/usr/bin/env python
# -*- coding: utf-8 -*-

import thread
import uuid

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from nx import *
from newsdb import NewsDB, create_db


class Article():
    def __init__(self, id_article=False, channel=False, db=False):
        self.id_article = id_article
        self._db = db
        if id_article:
            # load article from db
            db.query()
        else:
            self.guid = str(uuid.uuid1())
            self.content = {}
            self.source = "default"

    @property 
    def db(self):
        if not self._db:
            self._db = NewsDB()
        return self._db

    @property 
    def id(self):
        return self.id_article

    def save(self):
        if not self.id:
            db.query()




class ControlHandler(BaseHTTPRequestHandler):
    def log_request(self, code='-', size='-'): 
        pass 
       
    def _do_headers(self,mime="application/json", response=200, headers=[]):
        self.send_response(response)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        for h in headers:
            handler.send_header(h[0],h[1])
        self.send_header('Content-type', mime)
        self.end_headers()
         
    def _echo(self,istring):
        self.wfile.write(istring.encode("utf-8"))

    def result(self, r):
        response, data = r
        self._do_headers(response=response)
        self._echo(json.dumps([response, data]))


    def error(self,response):
        self._do_headers(response=response)

    def do_GET(self):
        service = self.server.service
        self.result(service.stat())



class Service(ServicePrototype):
    def on_init(self):
        port = 42200
        db_path = "news.db"

        if not os.path.exists(db_path):
            create_db(db_path)

        self.news_db = NewsDB(db_path)

        self.server = HTTPServer(('',port), ControlHandler)
        self.server.service = self
        thread.start_new_thread(self.server.serve_forever,())


    def get_item(self, source, channel):
        pass

    def on_main(self):
        pass