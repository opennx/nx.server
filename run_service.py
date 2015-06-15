#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *

# Shared python libraries
from nx.plugins import plugin_path
if plugin_path:
    python_plugin_path = os.path.join(plugin_path, "python")
    if os.path.exists(python_plugin_path):
        sys.path.append(python_plugin_path)

if __name__ == "__main__":
    try:
        id_service = int(sys.argv[1])
    except:
        critical_error("You must provide service id as first parameter")

    db = DB()
    db.query("SELECT agent, title, host, loop_delay, settings FROM nx_services WHERE id_service=%d" % id_service)
    try:
        agent, title, host, loop_delay, settings = db.fetchall()[0]
    except:
        critical_error("Unable to start service %s. No such service" % id_service)

    config["user"] = title

    if host != HOSTNAME:
        critical_error("This service should not run here.")

    if settings:
        try:
            settings = ET.XML(settings)
        except:
            db.query("UPDATE nx_services SET autostart=0 WHERE id_service=%d" % id_service)
            db.commit()
            critical_error("Malformed settings XML")


    _module = __import__("services.%s" % agent, globals(), locals(), ["Service"], -1)
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
        except:
            logging.error("Unhandled exception:\n\n{}".format(traceback.format_exc()))
            time.sleep
            sys.exit(1)
