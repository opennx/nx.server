from nx import *
from nx.assets import *
from nx.items import *



def bin_refresh(bins, sender=False, db=False):
    if not db:
        db = DB()
    for id_bin in bins:
        cache.delete("b{}".format(id_bin))
    bq = ", ".join([str(b) for b in bins])
    changed_rundowns = []
    q = "SELECT e.id_channel, e.start FROM nx_events as e, nx_channels as c WHERE c.channel_type = 0 AND c.id_channel = e.id_channel AND id_magic in ({})".format(bq)
    print q
    db.query(q)
    for id_channel, start_time in db.fetchall():
        start_time = time.strftime("%Y-%m-%d",time.localtime(start_time))
        chg = [id_channel, start_time]
        if not chg in changed_rundowns:
            changed_rundowns.append(chg)
    if changed_rundowns:
        print "Affected rundowns: ", changed_rundowns
        messaging.send("rundown_change", {"sender":sender, "rundowns":changed_rundowns})
    return 202, "OK"

  
def hive_get_day_events(auth_key,params={}):
    id_channel = int(params.get("id_channel",1))
    date = params.get("date",time.strftime("%Y-%m-%d"))
    result = []
    for event in get_day_events(id_channel, date):
        result.append(event.meta)
    return 200, {"events": result}


def hive_set_day_events(auth_key, params={}):
    id_channel = int(params.get("id_channel",False))
    updated = created = deleted = 0
    
    for id_event in params.get("delete",[]):
        id_event = int(id_event)
        event = Event(id_event)
        if not event:
            logging.warning("Unable to delete non existent event ID {}".format(id_event))
            continue
        logging.info("Deleting {!r}".format(event))
        event.delete()
        deleted += 1
    
    for event_data in params.get("events",[]):
        id_event = event_data.get("id_object",False)
        if id_event:
            event = Event(id_event)
        else:
            event = Event()
            bin = Bin()
            bin.save()
            event["id_magic"] = bin.id
            event["id_channel"] = id_channel
        for key in event_data:
            event.meta[key] = event_data[key]
        event.save()

    return 202 , "Somewhat happened"



def hive_rundown(auth_key, params):
    date = params.get("date",time.strftime("%Y-%m-%d"))
    id_channel = int(params.get("id_channel",1))

    start_time = datestr2ts(date)
    end_time   = start_time + (3600*24)
    
    data = []
    db = DB()
    db.query("SELECT id_object FROM nx_events WHERE id_channel = %s AND start > %s AND start < %s ORDER BY start ASC", (id_channel, start_time, end_time))
    for id_event, in db.fetchall():
        event = Event(id_event)
        bin   = event.get_bin()

        event_meta = event.meta
        bin_meta   = bin.meta
        items = []

        for item in bin.items:
            i_meta = item.meta
            a_meta = item.get_asset().meta

            # ITEM STATUS
            if item.get_asset()["status"] != ONLINE:
                i_meta["rundown_status"] = 0
            else:
                id_playout = item["id_playout/{}".format(id_channel)]
                if not id_playout or Asset(id_playout)["status"] != ONLINE:
                    i_meta["rundown_status"] = 2
                else:
                    i_meta["rundown_status"] = 3


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
            if not asset: # + Accept conditions
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

