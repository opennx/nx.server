#!/usr/bin/env python
from nebula import *
from nx.objects import *

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
        obj = lclass(id_object, db=db)
        result[name].append(obj.meta)



f = open("dump.json", "w")
json.dump(result, f)

