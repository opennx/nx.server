from .asset_states import *
from .channel_types import *
from .job_states import *
from .media_types import *
from .response_codes import *
from .run_modes import *
from .service_states import *
from .storage_types import *

#
# Following constants differ in version 4 and 5
#

ASSET = 0
ITEM  = 1
BIN   = 2
EVENT = 3
USER  = 4

OBJECT_TYPES = {
    "asset"  : 0,
    "item"   : 1,
    "bin"    : 2,
    "event"  : 3,
    "user"   : 4
}

#
# content types
#

TEXT     = 0
VIDEO    = 1
AUDIO    = 2
IMAGE    = 3

CONTENT_TYPES = {
    "text"  : TEXT,
    "video" : VIDEO,
    "audio" : AUDIO,
    "image" : IMAGE
}

#
# meta_classes
#

TEXT         = 0       # Single-line plain text (default)
BLOB         = 1       # Multiline text. 'syntax' can be provided in config
INTEGER      = 2       # Integer only value (for db keys etc)
NUMERIC      = 3       # Any integer of float number. 'min', 'max' and 'step' values can be provided in config
BOOLEAN      = 4       # 1/0 checkbox
DATETIME     = 5       # Date and time information. Stored as timestamp
TIMECODE     = 6       # Timecode information, stored as float(seconds), presented as HH:MM:SS:FF or HH:MM:SS.CS (centiseconds)
REGIONS      = 7
FRACTION     = 8       # 16/9 etc...
SELECT       = 9       # Select box ops stored as {'value':'title', 'another_value':'another title'}
CS_SELECT    = 10
ENUM         = 11      # Similar to select - for integer values
CS_ENUM      = 12

