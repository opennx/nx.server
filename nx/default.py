from constsants import *

#
# This is basic 
# Feel free to adjust variant, language and state configs according to your needs
#


BASE_META_SET = {

#
# a namespace:
# Asset data.
#

("a",  "id_asset",             0, 0, INTEGER,    False),
("a",  "media_type",           0, 0, SELECT,     {FILE:"File",VIRTUAL:"Virtual"}),
("a",  "content_type",         0, 0, SELECT,     {VIDEO:"Video",AUDIO:"Audio",IMAGE:"Image",TEXT:"Text"}),
("a",  "folder",               1, 0, FOLDER,     False),
("a",  "ctime",                0, 0, DATETIME,   False),
("a",  "mtime",                0, 0, DATETIME,   False),
("a",  "variant",              0, 0, SELECT,     {"Import"     : "Import",         #
												  "Acquisition": "Acquisition",    #
												  "Library"    : "Library",        # 
												  "Ingest"     : "Ingest",         # Material ingested by Ingest service
												  "Edit"       : "Edit",           # Material imported from NLE in production format
												  "Playout 1"  : "Playout 1"       # Material loacated on first playout storage
												  }),
("a",  "version_of",           0, 0, INTEGER,    False),
("a",  "status",               0, 0, STATUS,     False),

#
# nx namespace:
# 
#

("nx", "storage",              1, 0, INTEGER,    False),
("nx", "path",                 1, 1, TEXT,       False),
("nx", "state",                1, 0, STATE,      {0:"New",
												  1:"Approved",
												  2:"Declined"
												  }),
("nx", "script/rundown",       1, 0, BLOB,       {"syntax":"python"}),
("nx", "mark_in",              1, 0, TIMECODE,   False),
("nx", "mark_out",             1, 0, TIMECODE    False),
("nx", "duration",             0, 0, DURATION,   False),
("nx", "subclips",             0, 0, REGIONS,    False),
("nx", "article",              1, 1, BLOB,       {"syntax":"md"}),

#
# ebu namespace:
# 
#

("ebu","title/*",              1, 1, TEXT,       False),
("ebu","alternativeTitle/*/*", 1, 1, TEXT,       False),
("ebu","identifier",           1, 1, TEXT,       False),
("ebu","language",             1, 0, SELECT,     {"cs-CZ":"Czech",
	                                              "en-US":"English"
	                                              }),
("ebu","date",                 1, 0, DATE,		 False),
("ebu","subject",              1, 1, COMBO,      []),
("ebu","description",          1, 1, BLOB,		 {"syntax":"off"}),
("ebu","coverage",             1, 1, BLOB,       {"syntax":"off"}), 
("ebu","rights",               1, 1, BLOB,       {"syntax":"off"}),
("ebu","version",              1, 1, TEXT,       False),
("ebu","source/*",             0, 1, TEXT,       False ),

#
# fmt namespace:
# Technical metadata 
#

("fmt","width",                0, 0, INTEGER, False),
("fmt","height",               0, 0, INTEGER, False),
("fmt","fps",                  0, 0, TEXT, False),
("fmt","codec/*",              0, 0, TEXT, False),
("fmt","codec/*",              0, 0, TEXT, False),

#
# qc Namespace:
# These metadata hold results of automated Quality controll process
#

("qc", "silences",             0, 0, REGIONS, False),
("qc", "blacks",               0, 0, REGIONS, False),
("qc", "statics",              0, 0, REGIONS, False)
}
