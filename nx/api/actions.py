from nx import *

def api_actions(**kwargs):
    asset_idss = kwargs.get("assets", [])
    if not asset_ids:
        return {"response" : 400, "message" : "No asset selected"}

    result = []
    db = DB()
    db.query("SELECT id_action, title, config FROM nx_actions ORDER BY id_action ASC")
    for id_action, title, cfg in db.fetchall():
        try:
            cond = xml(cfg).find("allow_if").text
        except:
            log_traceback()
            continue

        for id_asset in assets:
            asset = Asset(id_asset, db=db)
            if not eval(cond):
                break
        else:
            if user.has_right("job_control", id_action):
                result.append((id_action, title))

    return {'response' : 200, 'message' : 'OK', 'data' : result }
