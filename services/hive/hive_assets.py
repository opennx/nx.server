from nx import *
from nx.assets import *
from nx.jobs import send_to

def hive_browse(auth_key, params):
    db = DB()
    conds = []

    if params.get("fulltext", False):
        if config["db_driver"] == "postgres":
            # happy debugging...
            conds.append("id_object IN (SELECT id_object FROM nx_meta WHERE object_type=0 AND %s)" % " AND ".join(["unaccent(LOWER(value)) LIKE unaccent('%%%s%%')" % db.sanit(elm.lower()) for elm in params["fulltext"].split()]))
        else:
            conds.append("id_object IN (SELECT id_object FROM nx_meta WHERE object_type=0 AND %s)" % " AND ".join(["LOWER(value) LIKE '%%%s%%'"% db.sanit(elm.lower()) for elm in params["fulltext"].split()]))

    if conds:
        qcon = " WHERE %s" % " AND ".join(conds)
    else:
        qcon = ""

    query = "SELECT id_object FROM nx_assets%s" % qcon

    print query

    asset_data = []
    db.query(query)
    for id_asset, in db.fetchall():
        asset = Asset(id_asset)
        asset_data.append(asset.meta)
    
    if not asset_data:
        return 204, []
    else:
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