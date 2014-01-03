#!/usr/bin/env python
# -*- coding: utf-8 -*-

########################################################################
## Constants

# service states
STOPPED  = 0           # Service is stopped. Surprisingly.
STARTED  = 1           # Service is started and running
STARTING = 2           # Service start requested.
STOPPING = 3           # Service graceful stop requested. It should shutdown itself after current iteration
KILL     = 4           # Service force stop requested. Dispatch is about to kill -9 it

# content_type
TEXT     = 0           # Text is text... letters, words, sentenses. muhehe 
VIDEO    = 1           # Moving images. Whooooo
AUDIO    = 2           # Noise
IMAGE    = 3           # Static porn

CONTENT_TYPES = {
    "TEXT"  : TEXT,
    "VIDEO" : VIDEO,
    "AUDIO" : AUDIO,
    "IMAGE" : IMAGE
}

# media_type
FILE     = 0           # There is (or should be) physical file specified by 'storage' and 'path' metadata
VIRTUAL  = 1           # Asset exists only as DB record (macro, text...)

# asset status
OFFLINE  = 0           # Associated file does not exist
ONLINE   = 1           # File exists and is ready to use
CREATING = 2           # File exists, but was changed recently. It is no safe (or possible) to use it yet
TRASHED  = 3           # File has been moved to trash location.
RESET    = 4           # Reset metadata action has been invoked. Meta service will update/refresh auto-generated asset information.

# meta_classes
TEXT         = 0       # Single-line plain text (default)
INTEGER      = 1       # Integer only value (for db keys etc)
NUMERIC      = 2       # Any integer of float number. 'min', 'max' and 'step' values can be provided in config
BLOB         = 3       # Multiline text. 'syntax' can be provided in config
DATE         = 4       # Date information. Stored as timestamp, presented as YYYY-MM-DD or calendar
TIME         = 5       # Clock information Stored as timestamp, presened as HH:MM #TBD
DATETIME     = 6       # Date and time information. Stored as timestamp
TIMECODE     = 7       # Timecode information, stored as float(seconds), presented as HH:MM:SS.CS (centiseconds)
DURATION     = 8       # Similar to TIMECODE, Marks and subclips are visualized 
REGION       = 9       # Single time region stored as ///// TBD
REGIONS      = 10      # Multiple time regions stored as json {"region_name":(float(start_second),float(end_second), "second_region_name":(float(start_second),float(end_second)}
SELECT       = 11      # Select box ops stored as {'value':'title', 'another_value':'another title'}
ISELECT      = 12      # Select box with integer value {0:'title',1:'another title'}
LIST         = 13      # Similar to SELECT, but /w value=title ... ops stored as list [value1, value2, value3]
COMBO        = 14      # Similar to LIST. Free text can be also provided instead of predefined options
FOLDER       = 15      # Folder selector. Stored as int(id_folder), Represented as text / select. including color etc.
STATUS       = 16      # Asset status representation (with colors or icons). stored as int
STATE        = 17      # Asset approval state representation. stored as int
FILESIZE     = 18      # Stored as int, displayed as K, M... etc.
MULTISELECT  = 19      # Stored as json list. config is simialar to select
PART         = 20      # Part X of Y. Stored as (X,Y) JSON tuple, where X and Y are integers
BOOLEAN      = 22      # 1/0 checkbox
STAR         = 21      # Same as boolean, but representated as shiny star in browser.

# storage types

LOCAL    = 0
CIFS     = 1
NFS      = 2
FTP      = 3

# Job status (stored in nx_jobs/progress)

PENDING   = -1
COMPLETED = -2
FAILED    = -3
ABORTED   = -4

# Channel types

PLAYOUT   = 0
INGEST    = 1
CAMPAIGN  = 2

DEBUG       = 0
INFO        = 1
WARNING     = 2
ERROR       = 3
GOOD_NEWS   = 4


SUCCESS_OK                = 200
SUCCESS_CREATED           = 201
SUCCESS_ACCEPTED          = 202
SUCCESS_NOCONTENT         = 204
SUCCESS_PARTIAL           = 206

ERROR_BAD_REQUEST         = 400
ERROR_UNAUTHORISED        = 401
ERROR_NOT_FOUND           = 404

ERROR_INTERNAL            = 500
ERROR_NOT_IMPLEMENTED     = 503
ERROR_TIMEOUT             = 504
ERROR_SERVICE_UNAVAILABLE = 503



## Constants
########################################################################