#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *


if __name__ == "__main__":
    try:
        id_service = int(sys.argv[1])
    except:
        critical_error("You must provide service id as first parameter")

    from services.dummy import Service

    config["user"] = "Dummy"
    service = Service(42)
    service.onInit()

    while True:
        service.onMain()
        sleep(1)