#!/usr/bin/env python
# -*- coding: utf-8 -*-

DEBUG = True

if DEBUG:
    import socket
    HOSTNAME = socket.gethostname()

from nx.constants import *


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
("hive",  "Hive"  , HOSTNAME, 1, 5 ,"""<settings></settings>"""),
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
