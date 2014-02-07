from nx import *
from nx.common.metadata import meta_types

def hive_meta_types(auth_key, params):
    return 200, [meta_types[t].pack() for t in meta_types.keys()]


def hive_site_settings(auth_key,params):
    db = DB()
    db.query("SELECT key, value FROM nx_settings")
    result = {}
    for tag, value in db.fetchall():
        result[tag] = value
    return 200, result
