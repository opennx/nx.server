from nx import *

def api_create(**kwargs):
    ids = kwargs.get("ids", [])
    db = kwargs.get("db", DB())
    return {"response" : 501, "message" : "Not implemented"}


