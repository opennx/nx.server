#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx.constants import *
from nx.cs import *

#
# This is basic metadata set, which should be present.
# Feel free to adjust origin, language and state configuration according to your needs
#


BASE_META_SET = [


# NAMESPACE  TAG         EDITABLE SEARCHABLE CLASS   DEFAULT   SETTINGS

#
# "A" name space:
# Asset data. Stored in nx_assets db table
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
("a",  "origin",                0, 0, LIST,       "",        ["Import",         # Temporary material in watchfolders.
                                                              "Acquisition",    # 
                                                              "Library",        # Jingles, templates, reusable stuff, stock footage
                                                              "Ingest",         # Material ingested by Ingest service
                                                              "Edit",           # Material imported from NLE in production format
                                                              "Playout 1"       # Material loacated on first playout storage
                                                              ]),
("a",  "version_of",            0, 0, INTEGER,    0,         False),
("a",  "status",                0, 0, STATUS,     0,         False),
#
# "NX" namespace:
# 
#
("nx", "id_storage",            1, 0, INTEGER,    0,         False),
("nx", "path",                  1, 1, TEXT,       "",        False),
("nx", "script/rundown",        1, 0, BLOB,       "",        {"syntax":"python"}),
("nx", "mark_in",               1, 0, TIMECODE,   0,         False),
("nx", "mark_out",              1, 0, TIMECODE,   0,         False),
("nx", "subclips",              0, 0, REGIONS,    "[]",      False),
("nx", "article",               1, 1, BLOB,       "",        {"syntax":"md"}),
("nx", "promoted",              1, 0, STAR,       0,         False),              # Asset "promotion". It's hit, important, favourite,....
("nx", "meta_probed",           0, 0, BOOLEAN,    0,         False),              # If true, meta_probes would not overwrite non-technical metadata during update




("ebu", "title",                1, 1, TEXT,        "",       False),
("ebu", "alternativeTitle",     1, 1, TEXT,        "",       False),
("ebu", "identifier/main",      1, 1, TEXT,        "",       False),              # Primary unique indentifier (IDEC, GUID...)
("ebu", "identifier/youtube",   0, 1, TEXT,        "",       False),              # Youtube ID if exists
("ebu", "identifier/vimeo",     0, 1, TEXT,        "",       False),              # Vimeo ID if exists
("ebu", "identifier/imdb",      1, 1, TEXT,        "",       False),
("ebu", "language",             1, 0, SELECT,      "cs-CZ",  {"cs-CZ":"Czech",
                                                              "en-US":"English"
                                                             }),
("ebu", "date",                 1, 0, DATE,        0,        False),
("ebu", "genre",                1, 1, LIST,        "",       NX_GENRES),
("ebu", "genre/music",          1, 1, LIST,        "",       NX_MUSIC_GENRES), 
("ebu", "description",          1, 1, BLOB,        "",       {"syntax":"off"}),
("ebu", "coverage",             1, 1, BLOB,        "",       {"syntax":"off"}),
("ebu", "subject",              1, 1, BLOB,        "",       {"syntax":"off"}),   # Keywords
("ebu", "rights",               1, 1, BLOB,        "",       {"syntax":"off"}),
("ebu", "version",              1, 1, TEXT,        "",       False),
("ebu", "source",               0, 1, TEXT,        "",       False),
("ebu", "source/url",           0, 1, TEXT,        "",       False),

("ebu", "role/director",        1, 1, TEXT,        "",       False),              # ebu_RoleCode 20.16
("ebu", "role/composer",        1, 1, TEXT,        "",       False),              # ebu_RoleCode 17.1.7 (music)
("ebu", "role/performer",       1, 1, TEXT,        "",       False),              # ebu_RoleCode 17.2   (music)

("id3", "album",                1, 1, TEXT,        "",       False),
("id3", "album/track",          1, 0, INTEGER,     0,        False),
("id3", "album/disc",           1, 0, INTEGER,     0,        False),

#
# "FMT" name space:
# Technical metadata. 
# Should be reset on media file change
#
("fmt", "file/mtime",           0, 0, DATETIME,    0 ,       False),
("fmt", "file/size",            0, 0, FILESIZE,    0 ,       False),
("fmt", "format",               0, 0, TEXT,        "",       False),              # Container format name. from ffprobe/format/format_name
("fmt", "duration",             0, 0, DURATION,    0 ,       False),              # Clip duration. From ffprobe/format/duration. if fails, taken from streams[0]/duration
("fmt", "video/width",          0, 0, INTEGER,     0 ,       False),    
("fmt", "video/height",         0, 0, INTEGER,     0 ,       False),
("fmt", "video/fps",            0, 0, TEXT,        "",       False),
("fmt", "video/pixel_format",   0, 0, TEXT,        "",       False),
("fmt", "video/aspect_ratio",   0, 0, TEXT,        "",       False),
("fmt", "video/codec",          0, 0, TEXT,        "",       False),
("fmt", "audio/codec",          0, 0, TEXT,        "",       False),

#
# "QC" name space:
# These metadata hold results of automated Quality control process
# Should be reset on media file change
#

("qc", "qc/state",              1, 0, STATE,       0,        {0:"New",            # This is new, or freshly modified file
                                                              1:"QC Passed",      # Automated quality controll passed and everything is ok
                                                              1:"Approved",       # Someone (QC human) checked the file and it was ok
                                                              2:"Rejected"        # Someone (QC human) checked the file and it was baaaad
                                                              }),
("qc", "qc/report",             1, 0, BLOB,        "",       False),              # Holds error report from QC Pass and/or rejection/approval message from QC humanoid
("qc", "audio/bpm",             0, 0, FLOAT,       0,        False),
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





META_ALIASES = [
('id_asset'             , 'en-US', '#'),     
('media_type'           , 'en-US', 'Media type'),       
('content_type'         , 'en-US', 'Content type'),         
('id_folder'            , 'en-US', 'Folder'),      
('ctime'                , 'en-US', 'Created'),  
('mtime'                , 'en-US', 'Modified'),  
('origin'               , 'en-US', 'Origin'),   
('version_of'           , 'en-US', 'Version of'),       
('status'               , 'en-US', 'Status'),   
('id_storage'           , 'en-US', 'Storage'),       
('path'                 , 'en-US', 'Path'), 
('state'                , 'en-US', 'Approval'),  
('script/rundown'       , 'en-US', 'Script'),           
('mark_in'              , 'en-US', 'Mark in'),    
('mark_out'             , 'en-US', 'Mark out'),     
('subclips'             , 'en-US', 'Subclips'),     
('article'              , 'en-US', 'Text'),    
('title'                , 'en-US', 'Title'),  
('alternativeTitle'     , 'en-US', 'Alt. Title'),                 
('identifier/main'      , 'en-US', 'IDEC'),            
('identifier/youtube'   , 'en-US', 'Youtube ID'),               
('identifier/vimeo'     , 'en-US', 'Video ID'),             
('language'             , 'en-US', 'Language'),     
('date'                 , 'en-US', 'Date'), 
('genre/music'          , 'en-US', 'Genre'),
('role/performer'       , 'en-US', 'Artist'),
('description'          , 'en-US', 'Description'),        
('coverage'             , 'en-US', 'Coverage'),     
('rights'               , 'en-US', 'Rights'),   
('version'              , 'en-US', 'Version'),    
('album'                , 'en-US', 'Album'),    
('file/mtime'           , 'en-US', 'File changed'),       
('file/size'            , 'en-US', 'File size'),      
('format'               , 'en-US', 'Format'),   
('duration'             , 'en-US', 'Duration'),     

('id_asset'             , 'cs-CZ', '#'),     
('content_type'         , 'cs-CZ', 'Typ'),         
('id_folder'            , 'cs-CZ', 'Složka'),      
('ctime'                , 'cs-CZ', 'Vytvořeno'),  
('mtime'                , 'cs-CZ', 'Změněno'),  
('status'               , 'cs-CZ', 'Stav'),   
('qc/state'             , 'cs-CZ', 'Schválení'),  
('article'              , 'cs-CZ', 'Text'),    
('title'                , 'cs-CZ', 'Název'),  
('identifier/main'      , 'cs-CZ', 'IDEC'),            
('identifier/youtube'   , 'cs-CZ', 'Youtube ID'),               
('identifier/vimeo'     , 'cs-CZ', 'Video ID'),             
('language'             , 'cs-CZ', 'Jazyk'),     
('date'                 , 'cs-CZ', 'Pořízeno'), 
('genre'                , 'cs-CZ', 'Žánr'),
('description'          , 'cs-CZ', 'Popis'),        
('rights'               , 'cs-CZ', 'Práva'),   
('version'              , 'cs-CZ', 'Verze'),    
('file/mtime'           , 'cs-CZ', 'Soubor změněn'),       
('file/size'            , 'cs-CZ', 'Velikost'),      
('format'               , 'cs-CZ', 'Formát'),   
('duration'             , 'cs-CZ', 'Stopáž'),     
]



if __name__ == "__main__":
   for tag in BASE_META_SET:
      print tag[1]