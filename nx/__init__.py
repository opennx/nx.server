#!/usr/bin/env python
# -*- coding: utf-8 -*-
from nx.common import *
from nx.connection import *
from nx.services import *


def rights(auth_key, right=False):    
    default_rights = {
        "can/mcr" : [],               # (list of channels) - User can control playback of these channels
        "can/rundown_edit" : [],      # (list of channels) - 

        "can/view" : [],              # (list of views)
        "can/asset_edit" : [],        # (list of folders)  - User can edit assets in these folders
        "can/asset_create" : [],      # (list of folders)  - User can create asset in these folder (and can move assets which they can edit to this folders)
        "can/action" : [],            # (list of actions)  - User can start this type of action

        "can/service_control" : [],   # (list of services) - User can start/stop this service
        "can/service_edit" : []       # (list of services) - User can modify this service's settings
        }

    if True:
        r = {
            "can/mcr" : config["playout_channels"].keys(),
            "can/edit_rundown" : config["playout_channels"].keys(),
            "can/edit_asset" : range(0,100),
            "can/create_asset" : range(0,100),
            "can/action" : range(0,100),
            "can/view" : range(0,100),
            "can/service_control" : range(0,100)
            }

    default_rights.update(r)
    if right:
        return default_rights.get(right, False)
    return default_rights