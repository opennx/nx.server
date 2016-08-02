#!/usr/bin/env python
from nebula import *

def load_cache():
    db = DB()

    start_time = time.time()

    db.query("SELECT id_object, meta FROM nx_assets ORDER BY id_object DESC")
    for id_object, meta in db.fetchall():
        asset = Asset(id_object, db=db)
        if not meta:
            asset.save(set_mtime=False)

    db.query("SELECT id_object FROM nx_events WHERE start > %s ORDER BY start DESC", [time.time() - 3600*24*7 ])
    for id_object, in db.fetchall():
        e = Event(id_object, db=db)
        e.save()
        b = e.bin
        b.save(set_mtime=False)
        for item in b.items:
            logging.debug("saving {}".format(item))
            item.save(set_mtime=False)
    logging.goodnews("All objects loaded in {:.04f} seconds".format(time.time()-start_time))


if __name__ == "__main__":
    load_cache()
    time.sleep(1)
