from nx import *
from nx.assets import *
from nx.items import *

BLOCK_MODES = ["LINK", "MANUAL", "SOFT AUTO", "HARD AUTO"]



##################################################################################
## MACRO SCHEDULING BEGIN
  

def hive_get_events(auth_key, params={}):
    start_time = params.get("start_time", 0)
    end_time = params.get("end_time", start_time + (3600*24*7))
    extend = params.get("extend", False)
    id_channel = params.get("id_channel", False)

    if not id_channel:
        return 400, "No such playout channel"

    db = DB()
    db.query("SELECT id_object FROM nx_events WHERE id_channel = %s AND start >= %s AND start < %s ORDER BY start ASC", (id_channel, start_time, end_time))
    res = db.fetchall()

    if extend:
        db.query("SELECT id_object FROM nx_events WHERE id_channel = %s AND start < %s ORDER BY start DESC LIMIT 1", (id_channel, start_time))
        res = db.fetchall() + res

    result = []
    for id_event, in res:
        event = Event(id_event, db=db)
        pbin  = event.get_bin()
        event["duration"] = pbin.get_duration()
        result.append(event.meta)
    return 200, {"events" : result}



ASSET_TO_EVENT_INHERIT = [
    "title",          
    "title/subtitle", 
    "title/alternate",
    "title/series",   
    "title/original", 
    "description",    
    "promoted"
    ]


def hive_set_events(auth_key, params={}):
    delete = params.get("delete", [])
    events = params.get("events", [])
    id_channel = params.get("id_channel", False)

    db = DB()

    print events

    deleted = created = updated = 0
    for id_event in params.get("delete", []):
        event = Event(id_event, db=db)
        if not event:
            logging.warning("Unable to delete non existent event ID {}".format(id_event))
            continue
        pbin = event.get_bin()
        pbin.delete()
        event.delete()
        deleted += 1

    for event_data in params.get("events", []):
        id_event = event_data.get("id_object", False)
        if id_event:
            event = Event(id_event, db=db)
            updated +=1
        else:
            event = Event(db=db)
            pbin = Bin(db=db)
            pbin.save()
            event["id_magic"] = pbin.id
            event["id_channel"] = id_channel
            created +=1

        id_asset = event_data.get("id_asset", False)
        if id_asset and id_asset != event["id_asset"]:
            asset = Asset(id_asset, db=db)
            if asset:

                pbin.delete_childs(db=db)
                pbin.items = []
                
                if not event["dramatica/config"]:
                    item = Item(db=db)
                    item["id_asset"] = asset.id
                    item["position"] = 0
                    item["id_bin"] = pbin.id
                    item.save()
                    pbin.items.append(item)
                    pbin.save()
        
                event["id_asset"] = asset.id
                for key in ASSET_TO_EVENT_INHERIT:
                    if asset[key]:
                        event[key] = asset[key]

        for key in event_data:
            event.meta[key] = event_data[key]

        event.save()

    return 200, "TODO: Statistics"

## MACRO SCHEDULING END
##################################################################################
## MICRO SCHEDULING BEGIN



def hive_rundown(auth_key, params):
    start_time = params.get("start_time", 0)
    try:
        id_channel = int(params["id_channel"])
        channel_config = config["playout_channels"][id_channel]
    except:
        return 400, "No such playout channel"

    db = DB()
    end_time   = start_time + (3600*24)
    item_runs  = get_item_runs(id_channel, start_time, end_time, db=db)
    data = []

    db.query("SELECT id_object FROM nx_events WHERE id_channel = %s AND start >= %s AND start < %s ORDER BY start ASC", (id_channel, start_time, end_time))
    
    ts_broadcast = 0
    for id_event, in db.fetchall():
        event = Event(id_event)
        pbin  = event.get_bin()

        # Reset broadcast time indicator after empty blocks and if run mode is not AUTO (0)
        if not pbin.items:
            ts_broadcast = 0
        elif event["run_mode"]:
            ts_broadcast = 0

        event_meta = event.meta
        event_meta["rundown_scheduled"] = ts_scheduled = event["start"]
        event_meta["rundown_broadcast"] = ts_broadcast = ts_broadcast or ts_scheduled
        
        bin_meta   = pbin.meta
        items = []
        for item in pbin.items:
            i_meta = item.meta
            a_meta = item.get_asset().meta if item["id_asset"] else {}
            
            as_start, as_stop = item_runs.get(item.id, (0, 0))
            if as_start:
                ts_broadcast = as_start

            i_meta["rundown_scheduled"] = ts_scheduled
            i_meta["rundown_broadcast"] = ts_broadcast

            ts_scheduled += item.get_duration()
            ts_broadcast += item.get_duration()

            # ITEM STATUS
            #
            # -1 : AIRED
            # -2 : Partialy aired. Probably still on air or play service was restarted during broadcast
            #  0 : Master asset is offline. Show as "OFFLINE"
            #  1 : Master asset is online, but playout asset does not exist or is offline 
            #  2 : Playout asset is online. Show as "READY" 

            if as_start and as_stop:
                i_meta["rundown_status"] = -1 # AIRED
            elif as_start:
                i_meta["rundown_status"] = -2 #  PART AIRED
            elif not item["id_asset"]:
                i_meta["rundown_status"] = 2 # Virtual item or something... show as ready
            elif item.get_asset()["status"] != ONLINE:
                i_meta["rundown_status"] = 0 # Master asset is not online: Rundown status = OFFLINE
            else:
                id_playout = item["id_playout/{}".format(id_channel)]
                if not id_playout or Asset(id_playout)["status"] not in [ONLINE, CREATING]: # Master asset exists, but playout asset is not online.... (not scheduled / pending)
                    i_meta["rundown_status"] = 1
                else:
                    i_meta["rundown_status"] = 2 # Playout asset is ready

            items.append((i_meta, a_meta))



        data.append({
                "event_meta" : event_meta,
                "bin_meta"   : bin_meta,
                "items"      : items
            })

    return 200, {"data" : data}



def hive_bin_order(auth_key, params):
    id_bin = params.get("id_bin", False)
    order  = params.get("order", [])
    sender = params.get("sender", False)

    id_channel = params.get("id_channel", False) # Optional. Just for playlist-bin. 
    append_cond = "True"
    if id_channel:
        append_cond = config["playout_channels"][id_channel].get("rundown_accepts", "True")


    if not (id_bin and order):
        return 400, "Fuck you"

    affected_bins = [id_bin]
    pos = 1

    db = DB()
    for obj in order:
        object_type = obj["object_type"]
        id_object   = obj["id_object"]
        params      = obj["params"]

        if object_type == ITEM:
            if not id_object:
                item = Item(db=db)
                item["id_asset"] = obj["id_asset"]
                item.meta.update(obj.meta)
            else:
                item = Item(id_object, db=db)

            if not item["id_bin"] in affected_bins: 
                affected_bins.append(item["id_bin"])

        elif object_type == ASSET:
            asset = Asset(id_object, db=db)
            try:
                can_append = eval(append_cond)
            except:
                logging.error("Unable to evaluate rundown accept condition: {}".format(append_cond))
                continue
            if not asset or not can_append:
                continue

            item = Item(db=db)
            item["id_asset"] = asset.id
            item.meta.update(params)

        else:
            continue

        if not item or item["position"] != pos or item["id_bin"] != id_bin:
            item["position"] = pos
            item["id_bin"]   = id_bin
            item.save()
        pos += 1

    bin_refresh(affected_bins, sender, db)
    return 202, "OK"



def hive_del_items(auth_key,params):
    items = params.get("items",[])
    sender = params.get("sender", False)

    affected_bins = []
    db = DB()
    for id_item in items:
        item = Item(id_item, db=db)
        if not item["id_bin"] in affected_bins: 
                affected_bins.append(item["id_bin"])
        item.delete()

    bin_refresh(affected_bins, sender, db)
    return 202, "OK"



def hive_toggle_run_mode(auth_key,params={}):
    items  = list(params.get("items" ,[]))
    blocks = list(params.get("events" ,[]))
    affected_bins = set()
    if items:
        for id_item in items:
            item = Item(id_item)
            if not item["manual_start"]: 
                item["manual_start"] = 1
            else: 
                item["manual_start"] = 0
            item.save()
            affected_bins.append(item["id_bin"])
    elif events:
        for id_event in events:
            event = Event(id_event)
            event["run_mode"] = (event["run_mode"]+1) % len(BLOCK_MODES)
            event.save()
            affected_bins.append(event.get_bin().id)
    bin_refresh(list(affected_bins))
    return 200, "Run mode changed"
 