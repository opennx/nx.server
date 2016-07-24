from nx import *

def api_update(**kwargs):
    ids = kwargs.get("ids", [])
    db = kwargs.get("db", DB())
    return {"response" : 501, "message" : "Not implemented"}
