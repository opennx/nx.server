#!/usr/bin/env python
# -*- coding: utf-8 -*-

import thread
import uuid

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from nx import *
from nx.objects import *


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

    def result(self, data):
        self._do_headers()
        self._echo(json.dumps(data))


    def error(self,response):
        self._do_headers(response=response)

    def do_GET(self):
        service = self.server.service
        article = service.get_article(1, ["google_domov", "google_svet"])
        self.result(article.meta)



class Service(ServicePrototype):
    def on_init(self):
        port = 42200
        self.max_articles = 100

        self.history = {}
        self.server = HTTPServer(('',port), ControlHandler)
        self.server.service = self
        thread.start_new_thread(self.server.serve_forever,())


    def get_article(self, channel, groups):
        db = DB()
        db.query("""SELECT id_object FROM nx_assets WHERE id_folder = 6 AND mtime > {}
            AND id_object IN (SELECT id_object FROM nx_meta WHERE tag='news_group' AND value IN ({}))
            AND id_object IN (SELECT id_object FROM nx_meta WHERE tag='qc/state' AND value='4')
            """.format(time.time() - 86400,   ", ".join(["'{}'".format(group) for group in groups])))
        
        articles = [r[0] for r in db.fetchall()]

        if channel not in self.history:
            self.history[channel] = {}

        id_asset = sorted(articles, key=lambda id_asset: self.history[channel].get(id_asset, 0))[0]

        self.history[channel][id_asset] = time.time()

        article = Asset(id_asset)
        return article





    def get_free_asset(self, db=False):
        if not db:
            db=DB()

        db.query("SELECT COUNT(id_object) from nx_assets WHERE id_folder=6")
        count = db.fetchall()[0][0]
        if count < self.max_articles:
            return Asset(db=db)

        db.query("SELECT id_object FROM nx_assets WHERE id_folder = 6 ORDER BY mtime ASC LIMIT 1")
        return Asset(db.fetchall()[0][0], db=db)



    def on_main(self):
        from mod_google_headlines import google_headlines

        db = DB()
        for article in google_headlines():
            db.query("SELECT id_object FROM nx_meta WHERE tag='identifier/guid' AND value = %s AND id_object IN (SELECT id_object FROM nx_meta WHERE tag='news_group' AND value=%s )", [article["identifier/guid"], article["news_group"] ])
            if db.fetchall():
                continue

            db.query("SELECT id_object FROM nx_meta WHERE tag='title' AND value = %s AND id_object IN (SELECT id_object FROM nx_meta WHERE tag='news_group' AND value=%s )", [article["title"], article["news_group"] ])
            if db.fetchall():
                continue

            asset = self.get_free_asset(db=db)
            asset["id_folder"] = 6
            asset["origin"] = "News"
            asset["status"] = ONLINE
            asset["qc/state"] = 4
            asset.meta.update(article)
            asset.save()