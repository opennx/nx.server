from nx import *
from nx.assets import *

def hive_browse(auth_key, params):
    
    query = "SELECT id_asset FROM nx_assets"

    asset_data = []
    db = DB()
    db.query(query)
    for id_asset, in db.fetchall():
        asset = Asset(id_asset)
        asset_data.append(asset.meta)
    
    if not asset_data:
        return 204, []
    else:
        return 200, {"asset_data" : asset_data}