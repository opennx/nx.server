from nx import *
from nx.assets import *

def hive_browse(auth_key, params):

    db = DB()
    conds = []

    if "fulltext" in params:
        cond = "id_asset IN (SELECT id_asset FROM nx_meta WHERE value LIKE '%%%s%%')" % db.sanit(params["fulltext"])
        conds.append(cond)

    if conds:
        qcon += " WHERE %s" % " AND ".join(conds)
    else:
        qcon = ""

    query = "SELECT id_asset FROM nx_assets%s" % qcon

    asset_data = []
    db.query(query)
    for id_asset, in db.fetchall():
        asset = Asset(id_asset)
        asset_data.append(asset.meta)
    
    if not asset_data:
        return 204, []
    else:
        return 200, {"asset_data" : asset_data}