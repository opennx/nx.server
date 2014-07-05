from nx import *
from nx.assets import *
from nx.items import *

BLOCK_MODES = ["LINK", "MANUAL", "SOFT AUTO", "HARD AUTO"]



##################################################################################
## MACRO SCHEDULING BEGIN
  

def hive_get_day_events(auth_key,params={}):
    id_channel = int(params.get("id_channel",1))
    date = params.get("date",time.strftime("%Y-%m-%d"))
    num_days = params.get("num_days",1)
    result = []
    for event in get_day_events(id_channel, date, num_days):
        result.append(event.meta)
    return 200, {"events": result}


def hive_set_day_events(auth_key, params={}):
    id_channel = int(params.get("id_channel",False))
    updated = created = deleted = 0
    
    for id_event in params.get("delete", []):
        id_event = int(id_event)
        event = Event(id_event)
        if not event:
            logging.warning("Unable to delete non existent event ID {}".format(id_event))
            continue
        pbin = event.get_bin()
        pbin.delete()
        event.delete()
        deleted += 1
    
    for event_data in params.get("events",[]):
        id_event = event_data.get("id_object",False)
        if id_event:
            event = Event(id_event)
        else:
            event = Event()
            pbin = Bin()
            pbin.save()
            event["id_magic"] = pbin.id
            event["id_channel"] = id_channel
        for key in event_data:
            event.meta[key] = event_data[key]
        event.save()

    return 202 , "Somewhat happened"



def hive_event_from_asset(auth_key, params):
    id_asset = params.get("id_asset", False)
    id_channel = params.get("id_channel", False)
    timestamp = params.get("timestamp", False)
    asset = Asset(id_asset)

    if not (id_asset and id_channel and timestamp and asset):
        return 400, "e eeee"

    db = DB()
    
    event = Event(db=db)
    pbin = Bin(db=db)
    pbin.save()

    event["id_magic"] = pbin.id
    event["id_channel"] = id_channel
    event["start"] = timestamp
    event["title"] = asset["title"]
    event["promoted"] = asset["promoted"]
    event["description"] = asset["description"]
    event["dramatica/config"] = asset["dramatica/config"]
    event.save()
    
    if not event["dramatica/config"]:
        item = Item(db=db)
        item["id_asset"] = asset.id
        item["position"] = 0
        item["id_bin"] = pbin.id
        item.save()
        pbin.items.append(item)
        
    pbin.save()

    return 201, "Created"



def hive_scheduler(auth_key, params):
    date = params.get("date",time.strftime("%Y-%m-%d"))
    id_channel = int(params.get("id_channel",1))

    start_time = datestr2ts(date, *config["playout_channels"][id_channel].get("day_start", [6,0]))
    end_time   = start_time + (3600*24*7)

    db = DB()
    db.query("SELECT id_object FROM nx_events WHERE id_channel = %s AND start >= %s AND start < %s ORDER BY start ASC", (id_channel, start_time, end_time))
    res = db.fetchall()
    db.query("SELECT id_object FROM nx_events WHERE id_channel = %s AND start < %s ORDER BY start DESC LIMIT 1", (id_channel, start_time))
    res = db.fetchall() + res

    result = []
    for id_event, in res:
        event = Event(id_event)
        pbin  = event.get_bin()
        event["duration"] = pbin.get_duration()
        result.append(event.meta)
    return 200, {"data":result}



## MACRO SCHEDULING END
##################################################################################
## MICRO SCHEDULING BEGIN



def hive_rundown(auth_key, params):
    date = params.get("date",time.strftime("%Y-%m-%d"))
    id_channel = int(params.get("id_channel",1))

    db = DB()

    start_time = datestr2ts(date, *config["playout_channels"][id_channel].get("day_start", [6,0]))
    end_time   = start_time + (3600*24)
    ts_broadcast = 0
    data = []
    db.query("SELECT id_object FROM nx_events WHERE id_channel = %s AND start >= %s AND start < %s ORDER BY start ASC", (id_channel, start_time, end_time))
    for id_event, in db.fetchall():
        event = Event(id_event)
        pbin   = event.get_bin()

        event_meta = event.meta
        event_meta["rundown_scheduled"] = ts_scheduled = event["start"]
        if not ts_broadcast:
            ts_broadcast = ts_scheduled
        event_meta["rundown_broadcast"] = ts_broadcast

        if not pbin.items:
            ts_broadcast = 0

        bin_meta   = pbin.meta
        items = []

        for item in pbin.items:
            i_meta = item.meta
            a_meta = item.get_asset().meta if item["id_asset"] else {}
            
            i_meta["rundown_broadcast"] = ts_broadcast
            i_meta["rundown_scheduled"] = ts_scheduled
            ts_scheduled += item.get_duration()
            ts_broadcast += item.get_duration()

            # ITEM STATUS
            if not item["id_asset"]:
                i_meta["rundown_status"] = 2
            elif item.get_asset()["status"] != ONLINE:
                i_meta["rundown_status"] = 0
            else:
                id_playout = item["id_playout/{}".format(id_channel)]
                if not id_playout or Asset(id_playout)["status"] != ONLINE:
                    i_meta["rundown_status"] = 1
                else:
                    i_meta["rundown_status"] = 2

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
            item = Item(id_object, db=db)
            if not item:
                continue
            if not item["id_bin"] in affected_bins: 
                affected_bins.append(item["id_bin"])

        elif object_type == ASSET:
            asset = Asset(id_object, db=db)
            try:
                can_append = eval(append_cond)
            except:
                logging.error("Unable to evalueate rundown accept condition: {}".format(append_cond))
                continue
            if not asset or not can_append:
                continue

            item = Item(db=db)
            item["id_asset"] = asset.id
            item.meta.update(params)

        else:
            continue
        
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
 