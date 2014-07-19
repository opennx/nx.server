from nx import *
from nx.common.metadata import meta_types

def hive_meta_types(auth_key, params):
    return 200, [meta_types[t].pack() for t in meta_types.keys()]

def hive_site_settings(auth_key,params):
    db = DB()
    db.query("SELECT key, value FROM nx_settings WHERE key in ('seismic_addr', 'seismic_port')")
    result = {}
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

    return 200, result



def hive_services(auth_key, params):
    command    = params.get("command", 0) 
    id_service = params.get("id_service", 0)
    db = DB()
    if id_service and command in [STARTING, STOPPING, KILL]:
        db.query("UPDATE nx_services SET state = %s WHERE id_service = %s", [command, id_service])
        db.commit()
    res = []
    db.query("SELECT id_service, agent, title, host, autostart, loop_delay, settings, state, last_seen FROM nx_services ORDER BY id_service ASC")
    for id_service, agent, title, host, autostart, loop_delay, settings, state, last_seen in db.fetchall(): 
        s = {
            "id_service" : id_service, 
            "agent" : agent, 
            "title" : title, 
            "host" : host, 
            "autostart" : autostart, 
            "loop_delay" : loop_delay, 
            "settings" : settings, 
            "state" : state, 
            "last_seen" : time.time() - last_seen
        }
        res.append(s)   

    return 200, res
