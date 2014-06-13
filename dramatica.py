#!/usr/bin/env python

from nx import *
from nx.assets import Asset
from nx.items import Event, Bin, Item

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

def nx_history_connector(start=False,stop=False):
    db = DB()
    cond = ""
    if start:
        cond += " AND start > {}".format(start)
    if stop:
        cond += " AND stop < {}".format(start)
    db.query("SELECT id_object FROM nx_events WHERE id_channel in ({}) ORDER BY start ASC".format(", ".join([str(i) for i in config["playout_channels"] ])))
    for id_object, in db.fetchall():
        event = Event(id_object, db=db)
        ebin = event.get_bin()
        tstamp = event["start"]
        for item in ebin.items:
            tstamp += item.get_duration()
            yield (event["id_channel"], tstamp, item["id_asset"])





class Session():
    def __init__(self):
        self.cache = DramaticaCache(tags)
        stime = time.time()
        i = self.cache.load_assets(nx_assets_connector())
        logging.debug("{} assets loaded in {} seconds".format(i, time.time()-stime))
        self.rundown = False
        self.start_time = self.end_time = self.id_channel = 0

    def open_rundown(self, id_channel=1, date=time.strftime("%Y-%m-%d")):
        day_start = config["playout_channels"][id_channel].get("day_start", (6,0))

        self.id_channel = id_channel
        self.start_time = datestr2ts(date, *day_start)
        self.end_time = self.start_time + (3600*24)

        stime = time.time()
        i = self.cache.load_history(nx_history_connector())
        logging.debug("{} history items loaded in {} seconds".format(i, time.time()-stime))

        self.rundown = DramaticaRundown(
                self.cache,
                day=list(int(i) for i in date.split("-")),
                day_start=day_start,
                id_channel=id_channel
            )

        db = DB()
        db.query("SELECT id_object FROM nx_events WHERE id_channel = %s and start >= %s and start < %s ORDER BY start ASC", (id_channel, self.start_time, self.end_time))
        for id_event, in db.fetchall():
            event = Event(id_event, db=db)
            ebin = event.get_bin()

            block = DramaticaBlock(self.rundown, **event.meta)
            block.config = json.loads(block["dramatica/config"] or "{}")

            for eitem in ebin.items:
                item = self.cache[eitem["id_asset"]]
                block.add(item, **eitem.meta)


            self.rundown.add(block)


    def solve(self, id_event=False):
        """Solve one specified event, or entire rundown"""
        for block in self.rundown.blocks:
            if block.meta.get("id_event", -1) == id_event or id_event == False:
                self.cache.load_history(
                    nx_history_connector(start=self.start_time, stop=self.end_time),
                    start=self.start_time,
                    stop=self.end_time
                    )
                block.solve()

    def save(self):
        if not self.rundown:
            return

        for block in self.rundown.block:
            pass




if __name__ == "__main__":
    session = Session()
    session.open_rundown(date="2014-06-13")
    session.solve()
    print(session.rundown.__str__().encode("utf-8"))