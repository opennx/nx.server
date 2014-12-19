from nx import *
from nx.common.metadata import meta_types
from nx.objects import *
from .auth import sessions


REQUIRED_PROTOCOL = 140000

def hive_auth(auth_key, params):
    if params.get("protocol", 0) < REQUIRED_PROTOCOL:
        return [[400, "Your Firefly version is outdated.\nPlease download latest update from support website."]]

    if sessions[auth_key]:
        return [[200, "Already logged in"]]

    if params.get("login") and params.get("password"):
        db = DB()
        user = get_user(params["login"], params["password"], db=db)
        if user:
            db.query("INSERT INTO nx_sessions (key, id_user, host, ctime, mtime) VALUES (%s, %s , %s, %s, %s)", [ auth_key, user.id, params.get("host", "unknown"), time.time(), time.time()])
            db.commit()
            return [[200, "Logged in"]]
        else:
            return [[403, "Incorrect login/password combination"]]

    else:
        return [[403, "Not logged in"]]


def hive_logout(auth_key, params):
    user = sessions[auth_key]
    if not user:
        return [[403, "Not logged in"]]
    db = DB()
    db.query("DELETE FROM nx_sessions WHERE key = %s", [auth_key])
    db.commit()
    del sessions[auth_key]
    return [[200, "ok"]]


def hive_meta_types(auth_key, params):
    if not sessions[auth_key]:
        return [[403, "Not authorised"]]
    return [[200, [meta_types[t].pack() for t in meta_types.keys()]]]


def hive_site_settings(auth_key,params):
    if not sessions[auth_key]:
        return [[403, "Not authorised"]]
    db = DB()
    rights = sessions[auth_key].meta

    result = {}
    result["rights"] = rights

    db.query("SELECT key, value FROM nx_settings WHERE key in ('seismic_addr', 'seismic_port')")

    for tag, value in db.fetchall():
        result[tag] = value

    folders = {}
    db.query("SELECT id_folder, title, color, meta_set FROM nx_folders")
    for id_folder, title, color, meta_set in db.fetchall():
        folders[id_folder] = (title, color, json.loads(meta_set))
    result["folders"] = folders

    views = []
    db.query("SELECT id_view, title, config  FROM nx_views ORDER BY position")
    for id_view, title, view_config in db.fetchall():
        try:
            view_config = ET.XML(view_config)
            columns = [col.text for col in view_config.find("columns").findall("column")]
        except:
            columns = []
        views.append((id_view, title, columns))

    result["views"] = views

    result["playout_channels"] = {}
    result["ingest_channels"] = {}
    db.query("SELECT id_channel, channel_type, title, config FROM nx_channels")
    for id_channel, channel_type, title, ch_config in db.fetchall():
        try:
            ch_config = json.loads(ch_config)
        except:
            print ("Unable to parse channel {}:{} config.".format(id_channel, title))
            continue
        ch_config.update({"title":title})
        if channel_type == PLAYOUT:
            result["playout_channels"][id_channel] = ch_config
        elif channel_type == INGEST:
            result["ingest_channels"][id_channel] = ch_config

    cs = {}
    db.query("SELECT cs, value, label FROM nx_cs ORDER BY cs, value")
    for cstag, value, label in db.fetchall():
        if cstag not in cs:
            cs[cstag] = []
        cs[cstag].append([value, label])
    result["cs"] = cs

    return [[200, result]]


def hive_services(auth_key, params):
    if not sessions[auth_key]:
        return [[403, "Not authorised"]]
    command    = params.get("command", 0) 
    id_service = params.get("id_service", 0)
    db = DB()
    if id_service and command in [STARTING, STOPPING, KILL]:
        db.query("UPDATE nx_services SET state = %s WHERE id_service = %s", [command, id_service])
        db.commit()
    elif id_service and command == -1:
        db.query("UPDATE nx_services set autostart = CAST(NOT CAST(autostart AS boolean) AS integer) where id_service = {}".format(id_service))

    res = []
    db.query("SELECT id_service, agent, title, host, autostart, loop_delay, settings, state, last_seen FROM nx_services ORDER BY id_service ASC")
    for id_service, agent, title, host, autostart, loop_delay, settings, state, last_seen in db.fetchall(): 
        s = {
            "id_service" : id_service, 
            "agent" : agent, 
            "title" : title, 
            "host" : host, 
            "autostart" : bool(autostart), 
            "loop_delay" : loop_delay, 
            "settings" : settings, 
            "state" : state, 
            "last_seen" : time.time() - last_seen
        }
        res.append(s)   
    return [[200, res]]


def hive_message(auth_key, params):
    user = sessions[auth_key]
    if not user:
        return [[403, "Not authorised"]]

    if params.get("message", False):
        messaging.send("message", sender=auth_key, from_user=user["full_name"] or user["login"] , message=params["message"])
    return [[200, "ok"]]
