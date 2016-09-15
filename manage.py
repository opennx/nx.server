#!/usr/bin/env python

from __future__ import print_function

import os
import sys

from nebula import *

def dump():

    result = {
        "assets" : [],
        "items" : [],
        "bins" : [],
        "events" : [],
        "cs" : [],
        "folders" : [],
        "users" : [],
        }

    sets = [
            ["assets", Asset],
            ["items", Item],
            ["bins", Bin],
            ["events", Event],
            ["users", User]
        ]

    db = DB()
    for name, oclass in sets:
        db.query("SELECT id_object FROM nx_{}".format(name))
        for id_object, in db.fetchall():
            obj = oclass(id_object, db=db)
            result[name].append(obj.meta)
    f = open("dump.json", "w")
    json.dump(result, f)



def recache():
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


def add_user():
    try:
        login = raw_input("Login: ").strip()
        password = raw_input("Password: ").strip()
        is_admin = raw_input("Is it admin (yes/no): ").strip()
    except KeyboardInterrupt:
        print()
        logging.info("Aborted")
        sys.exit(0)
    u = User()
    u["login"] = u["full_name"] = login
    u["is_admin"] = "true" if is_admin == "yes" else ""
    u.set_password(password)
    u.save()
    print()
    logging.goodnews("User created")




if __name__ == "__main__":
    methods = {
            "dump" : dump,
            "recache" : recache,
            "adduser" : add_user
        }
    if len(sys.argv) != 2:
        critical_error("This command takes exactly one argument")
    method = sys.argv[1]
    if not method in methods:
        critical_error("Unknown method '{}'".format(method))
    logging.info("Executing '{}'".format(method))
    methods[method]()
