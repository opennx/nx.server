#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx.constants import *

#
# This is basic metadata set, which should be present.
# Feel free to adjust variant, language and state configuration according to your needs
#

BASE_META_SET = [

#
# "A" name space:
# Asset data.
#

("a",  "id_asset",              0, 0, INTEGER,    False),
("a",  "media_type",            0, 0, ISELECT,    {FILE   : "File",
                                                   VIRTUAL: "Virtual"
                                                   }),
("a",  "content_type",          0, 0, ISELECT,    {VIDEO : "Video",
                                                   AUDIO : "Audio",
                                                   IMAGE : "Image",
                                                   TEXT  : "Text"
                                                   }),
("a",  "id_folder",             1, 0, FOLDER,     False),
("a",  "ctime",                 0, 0, DATETIME,   False),
("a",  "mtime",                 0, 0, DATETIME,   False),
("a",  "variant",               0, 0, SELECT,     {"Import"     : "Import",         # Temporary material in watchfolders.
                                                   "Acquisition": "Acquisition",    # 
                                                   "Library"    : "Library",        # Jingles, templates, reusable stuff, stock footage
                                                   "Ingest"     : "Ingest",         # Material ingested by Ingest service
                                                   "Edit"       : "Edit",           # Material imported from NLE in production format
                                                   "Playout 1"  : "Playout 1"       # Material loacated on first playout storage
                                                   }),
("a",  "version_of",            0, 0, INTEGER,    False),
("a",  "status",                0, 0, STATUS,     False),

#
# "NX" namespace:
# 
#

("nx", "id_storage",            1, 0, INTEGER,    False),
("nx", "path",                  1, 1, TEXT,       False),
("nx", "state",                 1, 0, STATE,      {0:"New",
                                                   1:"Approved",
                                                   2:"Declined"
                                                   }),
("nx", "script/rundown",        1, 0, BLOB,       {"syntax":"python"}),
("nx", "mark_in",               1, 0, TIMECODE,   False),
("nx", "mark_out",              1, 0, TIMECODE,   False),
("nx", "subclips",              0, 0, REGIONS,    False),
("nx", "article",               1, 1, BLOB,       {"syntax":"md"}),

#
# "EBU" name space:
# 
#

("ebu", "title",                1, 1, TEXT,       False),
("ebu", "alternativeTitle/*/*", 1, 1, TEXT,       False),
("ebu", "identifier",           1, 1, TEXT,       False),
("ebu", "language",             1, 0, SELECT,     {"cs-CZ":"Czech",
                                                   "en-US":"English"
                                                   }),
("ebu", "date",                 1, 0, DATE,       False),
("ebu", "subject",              1, 1, COMBO,      []),
("ebu", "description",          1, 1, BLOB,       {"syntax":"off"}),
("ebu", "coverage",             1, 1, BLOB,       {"syntax":"off"}), 
("ebu", "rights",               1, 1, BLOB,       {"syntax":"off"}),
("ebu", "version",              1, 1, TEXT,       False),
("ebu", "source/*",             0, 1, TEXT,       False ),

#
# "FMT" name space:
# Technical metadata. 
# Should be reset on media file change
#

("fmt", "file/mtime",           0, 0, DATETIME,   False),
("fmt", "file/size",            0, 0, FILESIZE,   False),
("fmt", "duration",             0, 0, DURATION,   False),
("fmt", "width",                0, 0, INTEGER,    False),
("fmt", "height",               0, 0, INTEGER,    False),
("fmt", "fps",                  0, 0, TEXT,       False),
("fmt", "codec/*",              0, 0, TEXT,       False),

#
# "QC" name space:
# These metadata hold results of automated Quality control process
# Should be reset on media file change
#

("qc", "audio/r128/i",          0, 0, NUMERIC, False),   # Integrated loudness (LUFS)
("qc", "audio/r128/t",          0, 0, NUMERIC, False),   # Integrated loudness threshold (LUFS)
("qc", "audio/r128/lra",        0, 0, NUMERIC, False),   # LRA (LU) 
("qc", "audio/r128/lra/t",      0, 0, NUMERIC, False),   # Loudness range threshold (LUFS)
("qc", "audio/r128/lra/l",      0, 0, NUMERIC, False),   # LRA Low (LUFS)
("qc", "audio/r128/lra/r",      0, 0, NUMERIC, False),   # LRA High (LUFS)
("qc", "audio/silence",         0, 0, REGIONS, False),   # Areas with silent audio
("qc", "audio/clipping",        0, 0, REGIONS, False),   # Audio clipping areas
("qc", "video/black",           0, 0, REGIONS, False),   # Areas where video is black-only
("qc", "video/static",          0, 0, REGIONS, False)    # Areas with static image
]
