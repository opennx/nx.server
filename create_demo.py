#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from nx.common import *

from default_db import *
from default_meta import *



## key, value
SITE_SETTINGS = [
    ("seismic_addr" , "224.168.2.8"),
    ("seismic_port" , "42112"),
    ("cache_driver" , "null"),
    ("cache_host"   , "192.168.32.32"),
    ("cache_port"   , "11211")
]


## id_folder, title, color
FOLDERS = [
(1, "Music"       , 0xe34931),
(2, "Movies"      , 0x019875),
(3, "Jingles"     , 0xeec050),
(4, "Templates"   , 0x5b5da7),
(5, "Trailers"    , 0x9c2336),
]


## agent, title, host, autostart, loop_delay, settings
SERVICES = [
("meta" , "Meta"  , HOSTNAME, 1, 5 ,"""<settings></settings>"""),
("admin", "Admin" , HOSTNAME, 1, 5 ,"""<settings></settings>"""),
("watch", "Watch" , HOSTNAME, 1, 10,
"""
<settings>
    <mirror>
         <id_storage>1</id_storage>
         <path>Acquisition/Music</path>
         <recursive>1</recursive>
         <filters>
              <filter>audio</filter>
         </filters> 
         <meta tag='origin'>Acquisition</meta>
         <meta tag='id_folder'>1</meta>
     </mirror>

    <mirror>
        <id_storage>1</id_storage>
        <path>Library/Jingles</path>
        <recursive>0</recursive>
        <meta tag='origin'>Library</meta>
        <meta tag='id_folder'>3</meta>
    </mirror>
</settings>
""")

]


## id_storage, title, protocol, path, login, password
STORAGES = [
(1, "Test", LOCAL, "c:\\martas\\nxstor\\", "", ""),
(2, "Playout", LOCAL, "c:\\martas\\opt\\Caspar\\media", "", "")
]






##############################################################  
## create db structure

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