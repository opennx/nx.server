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
    return [[200, {"result": db.fetchall(), "asset_data":[]}]]



def hive_get_assets(auth_key, params):
    asset_ids = params.get("asset_ids", [])
    db = DB()
    result = {}
    for i, id_asset in enumerate(asset_ids):
        asset = Asset(id_asset, db=db)
        yield -1, asset.meta
    yield 200, "OK"
    return



def hive_actions(auth_key, params):
    i = 0
    assets = params.get("assets", [])
    if not assets: 
        return [[400, "No asset selected"]]
        
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
    return [[200, result]]



def hive_send_to(auth_key, params):
    db = DB()
    try:
        id_action = params["id_action"]
    except:
        yield 400, "No action specified"
        return

    settings  = params.get("settings", {})
    restart_existing = params.get("restart_existing", True)

    for id_object in params.get("objects", []):
        yield -1, send_to(id_object, id_action, settings={}, id_user=0, restart_existing=restart_existing, db=db)[1]
    yield 200, "OK"
    return



def hive_set_meta(auth, params):
    objects = [int(id_object) for id_object in params.get("objects",[])]
    object_type = params.get("object_type","asset")
    data = params.get("data", {})
    db = DB()
    changed_objects = []
    affected_bins = []
    for id_object in objects:

        create_script = False
        if object_type == "asset" and not id_object:
            if not data["id_folder"]:
                msg = "You must select asset folder"
                logging.warning(msg)
                return [[400, msg]]
            db.query("SELECT create_script FROM nx_folders WHERE id_folder=%s", [data["id_folder"]])
            try:
                create_script = db.fetchall()[0][0]
            except:
                msg ="Unable to load create_script"
                logging.warning(msg)
                return [[400, msg]]         
            if not create_script:       
                msg = "It is not possible create this kind of asset"
                logging.warning(msg)
                return [[400, msg]]

        obj = {
            "asset" : Asset,
            "item"  : Item,
            "bin"   : Bin,
            "event" : Event,
            }[object_type](id_object, db=db)

        changed = False
        for key in data:
            value = data[key]
            if obj[key] != value:
                obj[key] = value
                changed = True

        print ("CREATE_SCRIPT", create_script)

        if changed:
            changed_objects.append(obj.id)
            obj.save(notify=False)
            if object_type == "item" and obj["id_bin"] not in affected_bins:
                affected_bins.append(obj["id_bin"])

    if affected_bins:
        bin_refresh(affected_bins, db=db)

    messaging.send("objects_changed", objects=changed_objects, object_type=object_type, user="anonymous Firefly user") # TODO
    return [[200, obj.meta]]

def hive_trash(auth, params):
    objects = [int(id_object) for id_object in params.get("objects",[])]
    db = DB()
    for id_asset in objects:
        # TODO: CHeck if asset is not scheduled for playback
        asset = Asset(id_asset, db=db)
        asset["status"] = TRASHED
        asset.save()

    return [[200, "OK"]]