from nx import *
from nx.assets import *

def hive_browse(auth_key, params):
    db = DB()
    conds = []

    if params.get("fulltext", False): # I'll definitely go to hell
        if config["db_driver"] == "postgres":
            conds.append("id_asset IN (SELECT id_object FROM nx_meta WHERE %s)" % " AND ".join(["unaccent(LOWER(value)) LIKE unaccent('%%%s%%')"% db.sanit(elm.lower()) for elm in params["fulltext"].split()]))
        else:
            conds.append("id_asset IN (SELECT id_object FROM nx_meta WHERE %s)" % " AND ".join(["LOWER(value) LIKE '%%%s%%'"% db.sanit(elm.lower()) for elm in params["fulltext"].split()]))

    if conds:
        qcon = " WHERE %s" % " AND ".join(conds)
    else:
        qcon = ""

    query = "SELECT id_asset FROM nx_assets%s" % qcon

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