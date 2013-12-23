#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from nx.server import *

NX_ROOT = os.path.split(sys.argv[0])[0]
if not NX_ROOT in sys.path:
    sys.path.append(NX_ROOT)


from installer.default_db import *
from installer.default_meta import *
from installer.default_settings import *


##############################################################  
## create db structure

if os.path.exists(".cache"):
    try:    os.remove(".cache")
    except: pass

if os.path.exists(config["db_host"]):
    try:    os.remove(config["db_host"])
    except: critical_error("Unable to remove old DB File")

db = DB()
for q in SQLITE_TPL:
    db.query(q)
db.commit()

## create db structure
##############################################################
## metadata set

for ns, tag, editable, searchable, class_, default, settings in BASE_META_SET:
    print "%s/%s"%(ns,tag)
    q = """INSERT INTO nx_meta_types (namespace, tag, editable, searchable, class, default_value, settings) VALUES ('%s' ,'%s', %d, %d, %d, '%s', '%s')""" % \
           (ns, tag, editable, searchable, class_, default, json.dumps(settings))
    db.query(q)

for tag, lang, alias in META_ALIASES:
    q = """INSERT INTO nx_meta_aliases (tag, lang, alias) VALUES ('%s' ,'%s', '%s')""" % (tag, lang, alias)
    db.query(q)
    
db.commit()

## metadata set
##############################################################
## site settings

for key, value in SITE_SETTINGS:
    q = """INSERT INTO nx_settings(key,value) VALUES ('%s','%s')""" % (key, value)
    db.query(q)
db.commit()

## site settings
##############################################################
## folders

for id_folder, title, color in FOLDERS:
  q = "INSERT INTO nx_folders (id_folder, title, color) VALUES (%d,'%s',%d)" % (id_folder, title, color)
  db.query(q)
db.commit()

## folders
##############################################################
## services

for agent, title, host, autostart, loop_delay, settings in SERVICES:
    q = "INSERT INTO nx_services (agent, title, host, autostart, loop_delay, settings, state, pid, last_seen) VALUES ('%s','%s','%s',%d, %d, '%s',0,0,0)" % \
        (agent, title, host, autostart, loop_delay, db.sanit(settings))
    db.query(q)
db.commit()

## services
##############################################################
## storages

for id_storage, title, protocol, path, login, password in STORAGES:
    q = "INSERT INTO nx_storages (id_storage, title, protocol, path, login, password) VALUES (%d, '%s', %d, '%s', '%s', '%s')" % \
        (id_storage, db.sanit(title), protocol, db.sanit(path), db.sanit(login), db.sanit(password))
    db.query(q)
db.commit() 