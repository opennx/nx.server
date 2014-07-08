#!/usr/bin/env python

from nx import *
from nx.assets import Asset
from nx.items import Event, Bin, Item

from dramatica.common import DramaticaCache
from dramatica.scheduling import DramaticaBlock, DramaticaRundown
from dramatica.templates import DramaticaTemplate
from dramatica.timeutils import *

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
    db.query("SELECT id_object FROM nx_assets WHERE id_folder IN (1,2,3,4,5,7,8) AND media_type = 0 AND origin IN ('Library', 'Acquisition', 'Edit')")
    for id_object, in db.fetchall():
        asset = Asset(id_object, db=db)
        if str(asset["qc/state"]) == "3": # Temporary fix. qc/state is going to be reimplemented in nx.server
            continue
        yield asset.meta

def nx_history_connector(start=False, stop=False, tstart=False):
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



class NXTVTemplate(DramaticaTemplate):
    def apply(self):

        MAIN_GENRES = {
            MON : ["horror"], 
            TUE : ["political", "social", "conspiracy"],
            WED : ["arts"],
            THU : ["technology"],
            FRI : ["rock"],
            SAT : ["rock"],
            SUN : ["drama", "comedy"]
        }[self.dow]


        self.add_block("06:00", title="Morning mourning")
        self.configure(
            solver="MusicBlock", 
            genres=["Pop", "Rock", "Alt rock"]
            )

        self.add_block("10:00", title="Some movie")
        self.configure(
            solver="DefaultSolver"
            )   

        self.add_block("12:00", title="Rocking")
        self.configure(
            solver="MusicBlock",
            genres=["Rock"],
            intro_jingle="path LIKE '%vedci_zjistili%'",
            jingles="path LIKE '%vedci_zjistili%'"
            )   

        self.add_block("16:00", title="Another movie")
        self.configure(
            solver="DefaultSolver"
            )   

        self.add_block("19:00", title="PostX")
        self.configure(
            solver="MusicBlock",
            genres=["Alt rock"],
            intro_jingle="path LIKE '%postx_short%'",
            outro_jingle="path LIKE '%postx_short%'",
            jingles="path LIKE '%postx_short%'"
            )   

        self.add_block("21:00", title="Movie of the day")
        self.configure(
            solver="DefaultSolver",
            genres=MAIN_GENRES
            )   

        self.add_block("23:00", title="Nachtmetal")
        self.configure(
            solver="MusicBlock",
            genres=["Metal"],
            intro_jingle="path LIKE '%nachtmetal_intro%'",
            jingles="path LIKE '%nachtmetal_short%'",
            target_duration=dur("02:00:00"),
            run_mode=2
            )   








class Session():
    def __init__(self):
        self.cache = DramaticaCache(tags)
        stime = time.time()
        i = self.cache.load_assets(nx_assets_connector())
        logging.debug("{} assets loaded in {} seconds".format(i, time.time()-stime))
        self.rundown = False
        self.start_time = self.end_time = self.id_channel = 0

    def open_rundown(self, id_channel=1, date=time.strftime("%Y-%m-%d"), clear=False):
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

        if clear:
            self.clear()
            return

        db = DB()
        db.query("SELECT id_object FROM nx_events WHERE id_channel = %s and start >= %s and start < %s ORDER BY start ASC", (id_channel, self.start_time, self.end_time))
        for id_event, in db.fetchall():
            event = Event(id_event, db=db)
            ebin = event.get_bin()
            event.meta["id_event"] = event.id
            block = DramaticaBlock(self.rundown, **event.meta)
            block.config = json.loads(block["dramatica/config"] or "{}")

            for eitem in ebin.items:
                eitem.meta["id_item"] = eitem.id
                item = self.cache[eitem["id_asset"]]
                block.add(item, **eitem.meta)
            self.rundown.add(block)


    def solve(self, id_event=False):
        """Solve one specified event, or entire rundown"""
        if not id_event:
            self.rundown.solve()
        else:
            pass
            #TODO: Single event cleanup


  
    def save(self):
        if not self.rundown:
            return
        print ""

        db = DB()
        for block in self.rundown.blocks:
            if block["id_event"]:
                event = Event(block["id_event"], db=db)
                ebin = event.get_bin()
            else:
                event = Event(db=db)
                ebin = Bin(db=db)
                ebin.save()


            print ["New", "Updated"][bool(event.id)]
            print block["title"]
            print time.strftime("%H:%M", time.localtime(block["start"]))

            old_items = [item for item in ebin.items]

            for pos, bitem in enumerate(block.items):
                if bitem["id_item"]:
                    item = Item(bitem["id_item"], db=db)
                else:
                    item = Item(db=db)

                item["id_bin"] = ebin.id
                item["id_asset"] = bitem.id
                item["position"] = pos
                
                for key in ["mark_in", "mark_out", "promoted", "is_optional"]:
                    if bitem[key]:
                        item.meta[key] = bitem[key]

                item.save()
                ebin.items.append(item)

            for item in old_items:
                if item.id not in [i.id for i in ebin.items]:
                    item.delete()

            for key in block.meta:
                event[key] = block[key]

            ebin.save()
            event["id_magic"] = ebin.id
            event["id_channel"] = self.id_channel
            event["dramatica/config"] = json.dumps(block.config)
            event["start"] = block["start"]
            if "run_mode" in block.meta:
                event["run_mode"] = block["run_mode"]
            event.save()

            print "***********************************************"


    def clear(self):
        if not self.rundown:
            return
        db = DB()
        db.query("SELECT id_object FROM nx_events WHERE id_channel = %s and start >= %s and start < %s ORDER BY start ASC", (self.id_channel, self.start_time, self.end_time))
        for id_event, in db.fetchall():
            id_event = int(id_event)
            event = Event(id_event, db=db)
            if not event:
                logging.warning("Unable to delete non existent event ID {}".format(id_event))
                continue
            pbin = event.get_bin()
            pbin.delete()
            event.delete()




if __name__ == "__main__":
    session = Session()
    full = True
    session.open_rundown(date="2014-07-10", clear=full)
    #if full:
    #    template = NXTVTemplate(session.rundown)
    #    template.apply()

    #session.solve()
    #session.save()

    #print(session.rundown.__str__().encode("utf-8"))