from nx import *
from nx.assets import *

def hive_meta_types(auth_key, params):
    return 200, [meta_types[t].pack() for t in meta_types.keys()]


def hive_site_settings(auth_key,params):
    return 200, {}
