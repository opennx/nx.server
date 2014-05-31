#!/usr/bin/env python

from nx import *
from nx.assets import Asset

from dramatica.common import DramaticaCache
from dramatica.scheduling import DramaticaBlock, DramaticaRundown

tags = [
    (str, "title"),
    (str, "description"),
    (str, "genre/music"),
    (str, "genre/movie"),
    (str, "rights"),
    (str, "source"),
    (str, "identifier/vimeo"),
    (str, "identifier/youtube"),
    (str, "identifier/main"),
    (str, "role/performer"),
    (str, "role/director"),
    (str, "role/composer"),
    (str, "album"),
    (str, "path"),
    (int, "qc/state"),
    (int, "id_folder"),
    (float, "duration"),
    (float, "mark_in"),
    (float, "mark_out")
    ]


def nx_assets_connector():
    db = DB()
    db.query("SELECT id_object FROM nx_assets")
    for id_object, in db.fetchall():
        asset = Asset(id_object, db=db)
        if asset["origin"] not in ["Library", "Acquisition", "Edit"]:
            continue
        yield asset.meta

def nx_history_connector():
    db = DB()
    db.query("SELECT id_object FROM nx_events WHERE id_channel in ({}) ORDER BY start ASC".format(", ".join(config["playout_channels"].keys())))
    for id_object, in db.fetchall():
        event = Event(id_object, db=db)
        ebin = event.get_bin()
        tstamp = event["start"]
        for item in ebin.items:
            tstamp += item.get_duration()
            yield (event["id_channel"], tstamp, item["id_asset"])





class Session():
    def __init__(self):
        self.cache = DramaticaCache(tags, nx_assets_connector())
        self.rundown = False

    def open_rundown(self, id_channel, date=time.strftime("%Y-%m-%d")):
        day_start = config["playout_channels"][id_channel].get("day_start", (6,0))
        
        self.rundown = DramaticaRundown()
        db = DB()
        db.query("SELECT id_event FROM nx_")
        for id_event, in db.fetchall():
            block = DramaticaBlock({"id_event":id_event})
            self.rundown.add(block)

    def solve(self, id_event):
        for block in self.rundown.blocks:
            if block.get("id_event", False) == id_event:
                block.solve()

    def save(self):
        if not self.rundown:
            return