#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *

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
    service.onInit()


    while True:
        service.onMain()
        service.heartbeat()
        sleep(loop_delay)