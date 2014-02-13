from nx import *
from nx.assets import *
from nx.items import *


  
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

    return 200 , "whatever"



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
            items.append((i_meta, a_meta))

        data.append({
                "event_meta" : event_meta,
                "bin_meta"   : bin_meta,
                "items"      : items
            })

    print (data)
    return 200, {"data" : data}