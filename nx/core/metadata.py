import time

from nxtools import *

from .common import *
from .constants import *

__all__ = ["meta_types", "MetaType"]

if PYTHON_VERSION < 3:
    str_type = unicode
else:
    str_type = str

#
# Validators
#

class NebulaInvalidValueError(Exception):
    pass


def validate_string(meta_type, value):
    if type(value) in (int, float):
        return str(value)
    return to_unicode(value).strip()

def validate_text(meta_type, value):
    if type(value) in (int, float):
        return str(value)
    return to_unicode(value).strip()

def validate_integer(meta_type, value):
    try:
        value = int(value)
    except ValueError:
        raise NebulaInvalidValueError
    return value

def validate_numeric(meta_type, value):
    if type(value) in [int, float]:
        return value
    try:
        return float(value)
    except:
        raise NebulaInvalidValueError

def validate_boolean(meta_type, value):
    if value:
        return True
    return False

def validate_datetime(meta_type, value):
    return validate_numeric(meta_type, value)

def validate_timecode(meta_type, value):
    return validate_numeric(meta_type, value)

def validate_regions(meta_type, value):
    #TODO
    return value

def validate_fract(meta_type, value):
    value = value.replace(":", "/")
    split = value.split("/")
    assert len(split) == 2 and split[0].isdigit() and split[1].isdigit()
    return value

def validate_select(meta_type, value):
    #TODO
    return value


# v4 spec

def validate_select(meta_type, value, **kwargs):
    return value # TODO

def validate_cs_select(meta_type, value, **kwargs):
    return value # TODO

def validate_enum(meta_type, value, **kwargs):
    return int(value)

def validate_cs_enum(meta_type, value, **kwargs):
    return int(value)

#
# Humanizers
# functions returning a human readable representation of the meta value
# since it may be used anywhere (admin, front end) additional rendering params can be passed
#

def humanize_numeric(meta_type, value, **kwargs):
    return "{:.03d}".format(value)

def humanize_boolean(meta_type, value, **kwargs):
    #TODO: web version, qt version etc
    return ["no", "yes"][bool(value)]

def humanize_datetime(meta_type, value, **kwargs):
    time_format = kwargs.get("time_format", "%Y-%m-%d %H:%M")
    return time.strfitme(time_format, time.localtime(value))

def humanize_timecode(meta_type, value, **kwargs):
    return s2time(value)

def humanize_regions(meta_type, value, **kwargs):
    return "{} regions".format(len(value))



# v4 spec

def humanize_select(meta_type, value, **kwargs):
    return value # TODO

def humanize_cs_select(meta_type, value, **kwargs):
    return value # TODO

def humanize_enum(meta_type, value, **kwargs):
    return value # TODO

def humanize_cs_enum(meta_type, value, **kwargs):
    return value # TODO

#
# Puting it all together
#

class MetaType(object):
    def __init__(self, key, **kwargs):
        self.key = key
        self.settings = {
                "title" : key,
                "searchable" : False,
                "editable" : False,
                "class" : TEXT,
                "default" : "",
                "aliases" : {}
            }
        self.settings.update(kwargs)
        self.humanizer = {
                -1 : None,
                TEXT : None,
                BLOB : None,
                INTEGER : None,
                NUMERIC : humanize_numeric,
                BOOLEAN : humanize_boolean,
                DATETIME : humanize_datetime,
                TIMECODE : humanize_timecode,
                REGIONS : humanize_regions,
                FRACTION : None,
                SELECT : humanize_select,
                CS_SELECT : humanize_cs_select,
                ENUM : humanize_enum,
                CS_ENUM : humanize_cs_enum
            }[self["class"]]

        self.validator = {
                -1 : None,
                TEXT : validate_string,
                BLOB : validate_text,
                INTEGER : validate_integer,
                NUMERIC : validate_numeric,
                BOOLEAN : validate_boolean,
                DATETIME : validate_datetime,
                TIMECODE : validate_timecode,
                REGIONS : validate_regions,
                FRACTION : validate_fract,
                SELECT : validate_select,
                CS_SELECT : validate_cs_select,
                ENUM : validate_enum,
                CS_ENUM : validate_cs_enum
            }[self["class"]]

    def __getitem__(self, key):
        return self.settings[key]

    def __setitem__(self, key, value):
        self.settings[key] = value

    def update(self, data):
        if not data:
            return
        self.settings.update(data)

    @property
    def default(self):
        if self["default"]:
            return self["default"]
        elif self["class"] in [TEXT, BLOB, SELECT, CS_SELECT]:
            return ""
        elif self["class"] in [INTEGER, NUMERIC, BOOLEAN, DATETIME, TIMECODE, ENUM, CS_ENUM]:
            return 0
        elif self["class"] == REGIONS:
            return {}
        elif self["class"] == FRACTION:
            return "1/1"
        return None

    @property
    def default_alias(self):
        return self.key.replace("_"," ").capitalize()

    def alias(self, lang="en"):
        if lang in self.settings["aliases"]:
            return self.settings["aliases"][0]
        return self.default_alias

    def header(self, lang="en"):
        if lang in self.settings["aliases"]:
            return self.settings["aliases"][1]
        return self.default_alias

    def validate(self, value):
        if self.validator:
            return self.validator(self, value)
        return value

    def humanize(self, value, **kwargs):
        if not self.humanizer:
            return value
        return self.humanizer(self, value, **kwargs)



class MetaTypes():
    def __init__(self):
        self.data = {}
        self.nstagdict = {}

    def __getitem__(self, key):
        return self.data.get(key, MetaType(key))

    def __setitem__(self, key, value):
        self.data[key] = value

    def __iter__(self):
        return self.data.__iter__()

    @property
    def dump(self):
        return {key : self[key].settings for key in self.data.keys()}

    def load_from_dump(self, dump):
        self.data = {}
        for key in dump:
            self.data[key] = MetaType(key, dump[key])


    #
    # v4 specs: to be deprecated
    #

    def ns_tags(self, ns):
        """deprecated"""
        if not ns in self.nstagdict:
            result = []
            for tag in self:
                if self[tag]["namespace"] in ["o", ns]:
                    result.append(self[tag].key)
            self.nstagdict[ns] = result
        return self.nstagdict[ns]

    def format(self, key, value):
        """deprecated"""
        if key.startswith("can/"):
            return json.loads(value)
        if not key in self:
            return value
        mtype = self[key]
        if  key == "path":                return value.replace("\\","/")
        elif mtype["class"] == TEXT:        return value.strip()
        elif mtype["class"] == BLOB:        return value.strip()
        elif mtype["class"] == INTEGER:     return int(value)
        elif mtype["class"] == NUMERIC:     return float(value)
        elif mtype["class"] == BOOLEAN:     return int(value)
        elif mtype["class"] == DATETIME:    return float(value)
        elif mtype["class"] == TIMECODE:    return float(value)
        elif mtype["class"] == REGIONS:     return value if type(value) == dict else json.loads(value)
        elif mtype["class"] == FRACTION:    return str(value).strip().replace(":","/")
        elif mtype["class"] == SELECT:      return value
        elif mtype["class"] == CS_SELECT:   return value
        elif mtype["class"] == ENUM:        return int(value)
        elif mtype["class"] == CS_ENUM:     return int(value)
        elif mtype["class"] == SELECT:      return value
        elif mtype["class"] == CS_SELECT:   return value

        return value

    def unformat(self, key, value):
        """deprecated"""
        mtype = self[key]
        if type(value) in (list, dict):
            return json.dumps(value)
        elif mtype["class"] == REGIONS or key.startswith("can/"):
            return json.dumps(value)
        return value

#
#
#

meta_types = MetaTypes()
