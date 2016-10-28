from nx import *

def api_settings(**kwargs):
    return {'response' : 200, 'data' : config}

def api_meta_types(**kwargs):
    return {'response' : 200, 'data' : meta_types.dump}

