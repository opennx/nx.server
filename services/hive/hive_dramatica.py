import imp

from nx import *
from nx.objects import *
from nx.plugins import plugin_path

from dramatica.common import DramaticaCache
from dramatica.scheduling import DramaticaBlock, DramaticaRundown
from dramatica.templates import DramaticaTemplate
from dramatica.timeutils import *


NX_TAGS = [
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
    (float, "mark_out"),
    (float, "audio/bpm")
    ]

def get_template(tpl_name):
    fname = os.path.join(plugin_path, "dramatica_templates", "{}.py".format(tpl_name))
    if not os.path.exists(fname):
        logging.error("Template does not exist")
        return 
    py_mod = imp.load_source(tpl_name, fname)
    return py_mod.Template

def nx_assets_connector():
    db = DB()
    db.query("SELECT id_object FROM nx_assets WHERE id_folder IN (1,2,3,4,5,7,8) AND media_type = 0 AND content_type=1 AND origin IN ('Library', 'Acquisition', 'Edit')")
    for id_object, in db.fetchall():
        asset = Asset(id_object, db=db)
        yield asset.meta

def nx_history_connector(start=False, stop=False, tstart=False):
    db = DB()
    cond = ""
    if start:
        cond += " AND start > {}".format(start)
    if stop:
        cond += " AND stop < {}".format(start)
    db.query("SELECT id_object FROM nx_events WHERE id_channel in ({}){} ORDER BY start ASC".format(", ".join([str(i) for i in config["playout_channels"] ]), cond ))
    for id_object, in db.fetchall():
        event = Event(id_object, db=db)
        ebin = event.get_bin()
        tstamp = event["start"]
        for item in ebin.items:
            yield (event["id_channel"], tstamp, item["id_asset"])
            tstamp += item.get_duration()




class Session():
    def __init__(self):
        self.cache = DramaticaCache(NX_TAGS)
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
            yield "Loading event {}".format(event)
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
            for msg in self.rundown.solve():
                yield msg
        else:
            pass
            #TODO: Single event cleanup
  

    def save(self):
        if not self.rundown:
            return
        db = DB()
        for block in self.rundown.blocks:
            if block["id_event"]:
                event = Event(block["id_event"], db=db)
                ebin = event.get_bin()
            else:
                event = Event(db=db)
                ebin = Bin(db=db)
                ebin.save()

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

                yield "Saving {}".format(item)
                item.save()
                ebin.items.append(item)

            for item in old_items:
                yield "Removing {}".format(item)
                if item.id not in [i.id for i in ebin.items]:
                    item.delete()

            for key in block.meta:
                event[key] = block[key]

            ebin.save()
            event["id_magic"] = ebin.id
            event["id_channel"] = self.id_channel
            event["dramatica/config"] = json.dumps(block.config)
            event["start"] = block["start"]
            yield "Saving {}".format(event)
            event.save()

    def clear_rundown(self, id_channel, date):
        day_start = config["playout_channels"][id_channel].get("day_start", (6,0))
        start_time = datestr2ts(date, *day_start)
        end_time = start_time + (3600*24)
        logging.info("Clear rundown {}".format(time.strftime("%Y-%m-%d", time.localtime(start_time))))
        
        db = DB()
        db.query("SELECT id_object FROM nx_events WHERE id_channel = %s and start >= %s and start < %s ORDER BY start ASC", (id_channel, start_time, end_time))
        for id_event, in db.fetchall():
            id_event = int(id_event)
            event = Event(id_event, db=db)
            if not event:
                logging.warning("Unable to delete non existent event ID {}".format(id_event))
                continue
            pbin = event.get_bin()
            for item in pbin.items:
                yield "Deleting {}".format(item)
                item.delete()
            pbin.items = []
            pbin.delete()
            yield "Deleting {}".format(event)
            event.delete()



################################################################################################


def hive_dramatica(auth_key, params={}):
    id_channel = params["id_channel"]
    date = params["date"]
    session = Session()

    for msg in session.clear_rundown(id_channel=id_channel, date=date):
        yield -1, {"message":msg}

    for msg in session.open_rundown(id_channel=id_channel, date=date):
        yield -1, {"message":msg}

    template_class = get_template("nxtv_template")
    template = template_class(session.rundown)
    template.apply()

    for msg in session.solve():
        yield -1, {"message":msg}
    
    for msg in session.save():
        yield -1, {"message":msg}