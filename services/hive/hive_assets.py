import hashlib

from nx import *
from nx.objects import *
from nx.jobs import send_to

def hive_browse(auth_key, params):
    db = DB()
    conds = []

    id_view = params.get("view", 1)
    view_config = config["views"][id_view]

    if "folders" in view_config:
        conds.append("id_folder IN ({})".format(view_config["folders"]))
    if "media_types" in view_config:
        conds.append("media_type IN ({})".format(view_config["media_types"]))
    if "content_types" in view_config:
        conds.append("content_type IN ({})".format(view_config["content_types"]))
    if "origins" in view_config:
        conds.append("origin IN ({})".format(view_config["origins"]))
    if "statuses" in view_config:
        conds.append("status IN ({})".format(view_config["statuses"]))
    if "query" in view_config:
        conds.append("id_object in ({})".format(view_config["query"]))

    # TODO: PLEASE REWRITE ME
    if params.get("fulltext", False):
        fulltext_base = "id_object IN (SELECT id_object FROM nx_meta WHERE object_type=0 AND {})"
        element_base  = "unaccent(value) ILIKE unaccent('%{}%')"
        fulltext_cond = " AND ".join([element_base.format(db.sanit(elm)) for elm in params["fulltext"].split()])
        conds.append(fulltext_base.format(fulltext_cond))

    query_conditions = " WHERE {}".format(" AND ".join(conds)) if conds else ""
    query = "SELECT id_object, mtime FROM nx_assets{}".format(query_conditions)

    db.query(query)
    return 200, {"result": db.fetchall(), "asset_data":[]}



def hive_get_assets(auth_key, params):
    asset_ids = params.get("asset_ids", [])
    db = DB()
    result = {}
    for id_asset in asset_ids:
        asset = Asset(id_asset, db=db)
        result[id_asset] = asset.meta
    return 200, result



def hive_actions(auth_key, params):
    assets = params.get("assets", [])
    if not assets: 
        return 400, "No asset selected"
    result = []
    db = DB()
    db.query("SELECT id_action, title, config FROM nx_actions ORDER BY id_action ASC")
    for id_action, title, cfg in db.fetchall():
        try:
            cond = ET.XML(cfg).find("allow_if").text
        except:
            continue
        for id_asset in assets:
            asset = Asset(id_asset, db=db)
            if not eval(cond):
                break
        else:
            result.append((id_action, title))
    return 200, result



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
    objects = [int(id_object) for id_object in params.get("objects",[])]
    object_type = params.get("object_type","asset")
    tag   = params["tag"]
    value = params["value"]
    db = DB()
    for id_object in objects:
        obj = {
            "asset" : Asset,
            "item"  : Item,
            "bin"   : Bin,
            "event" : Event,
            }[object_type](id_object, db=db)

        obj[tag] = value
        obj.save(notify=False)

    messaging.send("objects_changed", objects=objects, object_type=object_type, user="anonymous Firefly user") # TODO
    return 200, obj.meta
