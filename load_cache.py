#!/usr/bin/env python
from nx import *
from nx.objects import *



def load_cache():
    db = DB()

    start_time = time.time()

    db.query("SELECT id_object FROM nx_assets ORDER BY id_object DESC")
    for id_object, in db.fetchall():
        Asset(id_object, db=db)

    db.query("SELECT id_object FROM nx_items ORDER BY id_object DESC")
    for id_object, in db.fetchall():
        Item(id_object, db=db)

    db.query("SELECT id_object FROM nx_bins ORDER BY id_object DESC")
    for id_object, in db.fetchall():
        Bin(id_object, db=db)
    
    db.query("SELECT id_object FROM nx_events ORDER BY id_object DESC")
    for id_object, in db.fetchall():
        Event(id_object, db=db)
    logging.goodnews("All objects loaded in {:.04f} seconds".format(time.time()-start_time))



if __name__ == "__main__":
    import thread
    while True:
        load_cache()
        time.sleep(1)
