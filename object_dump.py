#!/usr/bin/env python
import sys

from nebula import *

result = {
    "assets" : [],
    "items" : [],
    "bins" : [],
    "events" : [],
    "users" : [],

    "cs" : [],
    "folders" : [],
    "settings" : [],
    "views" : [],
    "channels" : [],
    }


sets = [
        ["assets", Asset],
        ["items", Item],
        ["bins", Bin],
        ["events", Event],
        ["users", User]
    ]


start_time = time.time()
db = DB()
for name, oclass in sets:
    print ("exporting {}".format(name))
    db.query("SELECT id_object FROM nx_{} ORDER by id_object DESC".format(name))
    for id_object, in db.fetchall():
        obj = oclass(id_object, db=db)
        result[name].append(obj.meta)

db.query("SELECT id_folder, title, color, meta_set, validator FROM nx_folders ")
for row in db.fetchall():
    result["folders"].append(row)

db.query("SELECT cs, value, label FROM nx_cs")
for row in db.fetchall():
    result["cs"].append(row)


db.query("SELECT key, value FROM nx_settings")
for row in db.fetchall():
    result["settings"].append(row)

db.query("SELECT id_view, title, owner, config, position FROM nx_views")
for row in db.fetchall():
    result["views"].append(row)

db.query("SELECT id_channel, channel_type, title, config FROM nx_channels")
for row in db.fetchall():
    result["channels"].append(row)


if len(sys.argv) > 1:
    fname = sys.argv[-1]
else:
    fname = "dump.json"

json.dump(result, open(fname, "w"))
logging.goodnews ("Export finished in {:.02f}".format(time.time() - start_time))
