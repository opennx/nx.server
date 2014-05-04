from nx import *
from nx.assets import *
from nx.jobs import send_to

def hive_browse(auth_key, params):
    db = DB()
    conds = []

    if params.get("fulltext", False):
        fulltext_base = "id_object IN (SELECT id_object FROM nx_meta WHERE object_type=0 AND {})"
        element_base  = "LOWER(unaccent(value)) LIKE LOWER(unaccent('%{}%'))"
        fulltext_cond = " AND ".join([element_base.format(db.sanit(elm)) for elm in params["fulltext"].split()])
        conds.append(fulltext_base.format(fulltext_cond))

    if params.get("view", False):
        conds.append("id_object in ({})".format(config["views"][params["view"]]["query"]))

    query_conditions = " WHERE {}".format(" AND ".join(conds)) if conds else ""
    query = "SELECT id_object FROM nx_assets{}".format(query_conditions)

    print query

    asset_data = []
    db.query(query)
    for id_asset, in db.fetchall():
        asset = Asset(id_asset)
        asset_data.append(asset.meta)
    
    return 200, {"asset_data" : asset_data}




def hive_send_to(auth_key, params):
    db = DB()
    try:
        id_action = params["id_action"]
    except:
        return 400, "No action specified"

    settings  = params.get("settings", {})
    restart_existing = params.get("restart_existing", True)

    for id_object in params.get("objects", []):
        print (id_object, send_to(id_object, id_action, settings={}, id_user=0, restart_existing=restart_existing, db=db))
    return 200, "OK"


def hive_set_meta(auth, params):
    try:
        id_object = int(params["id_object"])
        tag = params["tag"]
        value = params["value"]
    except:
        return 400, "bla bla"

    db = DB()
    # FIXME: Another object types
    obj = Asset(id_object)
    obj[tag] = value
    obj.save()
    return 200, obj.meta
