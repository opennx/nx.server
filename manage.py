#!/usr/bin/env python
#
#    This file is part of Nebula media asset management.
#
#    Nebula is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Nebula is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Nebula. If not, see <http://www.gnu.org/licenses/>.
#

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
    object_types = [
            ["nx_assets", Asset],
            ["nx_users", User],
            ["nx_items", Item],
            ["nx_bins", Bin],
            ["nx_events", Event]
        ]
    i = 0
    for table_name, ObjectClass in object_types:
        logging.info("Caching {}".format(table_name))
        db.query("SELECT id_object, meta FROM {} ORDER BY id_object DESC".format(table_name))
        for id_object, meta in db.fetchall():
            if not id_object:
                continue
            try:
                obj = ObjectClass(id_object, db=db)
                if not meta:
                    obj.save(set_mtime=False)
            except KeyboardInterrupt:
                print()
                logging.warning("Interrupted by user")
                break
            except Exception:
                log_traceback()
                print (obj.meta)
                sys.exit(-1)
            i += 1
        else:
            continue
        break
    logging.goodnews("{} objects loaded in {:.04f} seconds".format(i, time.time()-start_time))


def add_user():
    try:
        login = raw_input("Login: ").strip()
        password = raw_input("Password: ").strip()
        is_admin = raw_input("Is it admin (yes/no): ").strip()
    except KeyboardInterrupt:
        print()
        logging.warning("Interrupted by user")
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
