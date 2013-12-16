#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx.constants import *

#
# This is basic metadata set, which should be present.
# Feel free to adjust origin, language and state configuration according to your needs
#

BASE_META_SET = [

#
# "A" name space:
# Asset data.
#

("a",  "id_asset",              0, 0, INTEGER,    0,         False),
("a",  "media_type",            0, 0, ISELECT,    0,         {FILE   : "File",
                                                              VIRTUAL: "Virtual"
                                                              }),
("a",  "content_type",          0, 0, ISELECT,    0,         {VIDEO : "Video",
                                                              AUDIO : "Audio",
                                                              IMAGE : "Image",
                                                              TEXT  : "Text"
                                                              }),
("a",  "id_folder",             1, 0, FOLDER,     0,         False),
("a",  "ctime",                 0, 0, DATETIME,   0,         False),
("a",  "mtime",                 0, 0, DATETIME,   0,         False),
("a",  "origin",                0, 0, SELECT,     "",        {"Import"     : "Import",         # Temporary material in watchfolders.
                                                              "Acquisition": "Acquisition",    # 
                                                              "Library"    : "Library",        # Jingles, templates, reusable stuff, stock footage
                                                              "Ingest"     : "Ingest",         # Material ingested by Ingest service
                                                              "Edit"       : "Edit",           # Material imported from NLE in production format
                                                              "Playout 1"  : "Playout 1"       # Material loacated on first playout storage
                                                              }),
("a",  "version_of",            0, 0, INTEGER,    0,         False),
("a",  "status",                0, 0, STATUS,     0,         False)
#
# "NX" namespace:
# 
#
("nx", "id_storage",            1, 0, INTEGER,    0,         False),
("nx", "path",                  1, 1, TEXT,       "",        False),
("nx", "state",                 1, 0, STATE,      0,         {0:"New",                        # Approval level of the asset
                                                              1:"Approved",
                                                              2:"Declined"
                                                              }),
("nx", "state_by")              0, 0, INTEGER,    0,         False),                          # ID of the user who set current state (0 for machine default)
("nx", "script/rundown",        1, 0, BLOB,       "",        {"syntax":"python"}),
("nx", "mark_in",               1, 0, TIMECODE,   0,         False),
("nx", "mark_out",              1, 0, TIMECODE,   0,         False),
("nx", "subclips",              0, 0, REGIONS,    "[]",      False),
("nx", "article",               1, 1, BLOB,       ""         {"syntax":"md"}),
#
# "EBU" name space:
# 
#
("ebu", "title",                1, 1, TEXT,        "",       False),
("ebu", "alternativeTitle",     1, 1, TEXT,        "",       False),
("ebu", "identifier/main",      1, 1, TEXT,        "",       False),              # Primary unique indentifier (IDEC, GUID...)
("ebu", "identifier/youtube",   0, 1, TEXT,        "",       False),              # Youtube ID if exists
("ebu", "identifier/vimeo",     0, 1, TEXT,        "",       False),              # Vimeo ID if exists
("ebu", "language",             1, 0, SELECT,      "cs-CZ",  {"cs-CZ":"Czech",
                                                              "en-US":"English"
                                                             }),
("ebu", "date",                 1, 0, DATE,        0,        False),
("ebu", "genre",                1, 1, COMBO,       "",       []),                 # Combo based on urn:ebu:metadata-cs:ContentGenreCS 
("ebu", "description",          1, 1, BLOB,        "",       {"syntax":"off"}),
("ebu", "coverage",             1, 1, BLOB,        "",       {"syntax":"off"}), 
("ebu", "rights",               1, 1, BLOB,        "",       {"syntax":"off"}),
("ebu", "version",              1, 1, TEXT,        "",       False),
("ebu", "source",               0, 1, TEXT,        "",       False ),
#
# "FMT" name space:
# Technical metadata. 
# Should be reset on media file change
#
("fmt", "file/mtime",           0, 0, DATETIME,    0 ,       False),
("fmt", "file/size",            0, 0, FILESIZE,    0 ,       False),
("fmt", "format",               0, 0, TEXT,        "",       False),              # Container format name. from ffprobe/format/format_name
("fmt", "duration",             0, 0, DURATION,    0 ,       False),              # Clip duration. From ffprobe/format/duration. if fails, taken from streams[0]/duration
("fmt", "width",                0, 0, INTEGER,     0 ,       False),    
("fmt", "height",               0, 0, INTEGER,     0 ,       False),
("fmt", "fps",                  0, 0, TEXT,        0 ,       False),
("fmt", "codec/video",          0, 0, TEXT,        "",       False),
("fmt", "codec/audio",          0, 0, TEXT,        "",       False),
#
# "QC" name space:
# These metadata hold results of automated Quality control process
# Should be reset on media file change
#
("qc", "audio/r128/i",          0, 0, NUMERIC,     0,        False),              # Integrated loudness (LUFS)
("qc", "audio/r128/t",          0, 0, NUMERIC,     0,        False),              # Integrated loudness threshold (LUFS)
("qc", "audio/r128/lra",        0, 0, NUMERIC,     0,        False),              # LRA (LU) 
("qc", "audio/r128/lra/t",      0, 0, NUMERIC,     0,        False),              # Loudness range threshold (LUFS)
("qc", "audio/r128/lra/l",      0, 0, NUMERIC,     0,        False),              # LRA Low (LUFS)
("qc", "audio/r128/lra/r",      0, 0, NUMERIC,     0,        False),              # LRA High (LUFS)
("qc", "audio/silence",         0, 0, REGIONS,     "[]",     False),              # Areas with silent audio
("qc", "audio/clipping",        0, 0, REGIONS,     "[]",     False),              # Audio clipping areas
("qc", "video/black",           0, 0, REGIONS,     "[]",     False),              # Areas where video is black-only
("qc", "video/static",          0, 0, REGIONS,     "[]",     False)               # Areas with static image
]





META_ALIASES = []
('id_asset'             , 'cs-CZ', 'ID'),     
#('media_type'           , 'cs-CZ', ''),       
('content_type'         , 'cs-CZ', 'Typ'),         
('id_folder'            , 'cs-CZ', 'Složka'),      
('ctime'                , 'cs-CZ', 'Vytvořeno'),  
('mtime'                , 'cs-CZ', 'Změněno'),  
#('origin'               , 'cs-CZ', ''),   
#('version_of'           , 'cs-CZ', ''),       
('status'               , 'cs-CZ', 'Stav'),   
#('id_storage'           , 'cs-CZ', ''),       
#('path'                 , 'cs-CZ', ''), 
('state'                , 'cs-CZ', '??????????????????'),  
#('script/rundown'       , 'cs-CZ', ''),           
#('mark_in'              , 'cs-CZ', ''),    
#('mark_out'             , 'cs-CZ', ''),     
#('subclips'             , 'cs-CZ', ''),     
('article'              , 'cs-CZ', 'Text'),    
('title'                , 'cs-CZ', 'Název'),  
#('alternativeTitle/*/*' , 'cs-CZ', ''),                 
('identifier/main'      , 'cs-CZ', 'IDEC'),            
('identifier/youtube'   , 'cs-CZ', 'Youtube ID'),               
('identifier/vimeo'     , 'cs-CZ', 'Video ID'),             
('language'             , 'cs-CZ', 'Jazyk'),     
('date'                 , 'cs-CZ', 'Pořízeno'), 
('genre'                , 'cs-CZ', 'Žánr'),
('description'          , 'cs-CZ', 'Popis'),        
('coverage'             , 'cs-CZ', ''),     
('rights'               , 'cs-CZ', 'Práva'),   
('version'              , 'cs-CZ', ''),    
#('source/*'             , 'cs-CZ', ''),     
('file/mtime'           , 'cs-CZ', 'Soubor změněn'),       
('file/size'            , 'cs-CZ', 'Velikost'),      
('format'               , 'cs-CZ', 'Formát'),   
('duration'             , 'cs-CZ', 'Stopáž'),     
('width'                , 'cs-CZ', ''),  
('height'               , 'cs-CZ', ''),   
('fps'                  , 'cs-CZ', ''),
('codec/*'              , 'cs-CZ', ''),    
('audio/r128/i'         , 'cs-CZ', ''),         
('audio/r128/t'         , 'cs-CZ', ''),         
('audio/r128/lra'       , 'cs-CZ', ''),           
('audio/r128/lra/t'     , 'cs-CZ', ''),             
('audio/r128/lra/l'     , 'cs-CZ', ''),             
('audio/r128/lra/r'     , 'cs-CZ', ''),             
('audio/silence'        , 'cs-CZ', ''),          
('audio/clipping'       , 'cs-CZ', ''),           
('video/black'          , 'cs-CZ', ''),        
('video/static'         , 'cs-CZ', '')   
]



if __name__ == "__main__":
   for tag in BASE_META_SET:
      print tag[1]