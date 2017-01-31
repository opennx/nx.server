#!/usr/bin/env python
#
#    This file is part of Nebula media asset management.
#
#    Nebula is` free software: you can redistribute it and/or modify
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

logging.user = "Manager"

#
# Service / admin runner
#


def run(*args):
    id_service = args[0]
    try:
        id_service = int(id_service)
    except ValueError:
        critical_error("Service ID must be integer")

    db = DB()
    db.query("SELECT agent, title, host, loop_delay, settings FROM nx_services WHERE id_service=%s", [id_service])
    try:
        agent, title, host, loop_delay, settings = db.fetchall()[0]
    except IndexError:
        critical_error("Unable to start service {}. No such service".format(id_service))

    config["user"] = logging.user = title

    if host != config["host"]:
        critical_error("This service should not run here.")

    if settings:
        try:
            settings = xml(settings)
        except Exception:
            log_traceback()
            db.query("UPDATE nx_services SET autostart=0 WHERE id_service=%s", [id_service])
            db.commit()
            critical_error("Malformed settings XML")

    _module = __import__("services." + agent, globals(), locals(), ["Service"], -1)
    Service = _module.Service
    service = Service(id_service, settings)

    while True:
        try:
            service.on_main()
            last_run = time.time()
            while True:
                time.sleep(min(loop_delay, 2))
                service.heartbeat()
                if time.time() - last_run >= loop_delay:
                    break
        except (KeyboardInterrupt):
            sys.exit(0)
        except (SystemExit):
            break
        except:
            log_traceback()
            time.sleep(2)
            sys.exit(1)

#
# System utils
#

def dump(*args):
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


def recache(*args):
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

#
# Administration
#

def add_user(*args):
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
            "run" : run,
            "dump" : dump,
            "recache" : recache,
            "adduser" : add_user
        }

    if len(sys.argv) < 2:
        critical_error("This command takes at least one argument")
    method = sys.argv[1]
    args = sys.argv[2:]
    if not method in methods:
        critical_error("Unknown method '{}'".format(method))
    methods[method](*args)
