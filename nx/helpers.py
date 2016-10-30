from .core import *
from .connection import *
from .objects import *


def get_user(login, password, db=False):
    if not db:
        db = DB()
    db.query("SELECT id_object, meta FROM nx_users WHERE login=%s and password=%s", [login, get_hash(password)])
    for id_object, meta in db.fetchall():
        return User(meta=meta)
    logging.warning("Login failed for user {}".format(login))
    return False


def asset_by_path(id_storage, path, db=False):
    path = path.replace("\\", "/")
    if not db:
        db = DB()
    db.query("""SELECT id_object FROM nx_assets
                WHERE object_type = 0
                AND meta->>'id_storage' = %s
                AND meta->>'path' = '%s')
                """, [id_storage, path.replace("\\","/")])
    try:
        return db.fetchall()[0][0]
    except IndexError:
        return False



def asset_by_full_path(path, db=False):
    if not db:
        db = DB()
    for s in storages:
        if path.startswith(storages[s].local_path):
            return asset_by_path(s,path.lstrip(s.path),db=db)
    return False



def bin_refresh(bins, sender=False, db=False):
    if not bins:
        return 200, "No bin refreshed"
    if not db:
        db = DB()
    for id_bin in bins:
        cache.delete("b{}".format(id_bin))
    bq = ", ".join([str(b) for b in bins if b])
    changed_events = []
    db.query("SELECT e.id_object, e.id_channel, e.start FROM nx_events as e, nx_channels as c WHERE c.channel_type = 0 AND c.id_channel = e.id_channel AND id_magic in ({})".format(bq))
    for id_event, id_channel, start_time in db.fetchall():
        chg = id_event
        if not chg in changed_events:
            changed_events.append(chg)
    if changed_events:
        messaging.send("objects_changed", sender=sender, objects=changed_events, object_type="event")
    return 202, "OK"


def get_day_events(id_channel, date, num_days=1):
    start_time = datestr2ts(date, *config["playout_channels"][id_channel].get("day_start", [6,0]))
    end_time   = start_time + (3600*24*num_days)
    db = DB()
    db.query("SELECT id_object, meta FROM nx_events WHERE id_channel=%s AND start > %s AND start < %s ", (id_channel, start_time, end_time))
    for id_event, meta in db.fetchall():
        yield Event(meta=meta)


def get_bin_first_item(id_bin, db=False):
    if not db:
        db = DB()
    db.query("SELECT id_item FROM nx_items WHERE id_bin=%d ORDER BY position LIMIT 1" % id_bin)
    try:
        return db.fetchall()[0][0]
    except IndexError:
        return False


def get_item_event(id_item, **kwargs):
    db = kwargs.get("db", DB())
    db.query("""SELECT e.id_object, e.start, e.id_channel, e.meta FROM nx_items AS i, nx_events AS e WHERE e.id_magic = i.id_bin AND i.id_object = {} AND e.id_channel IN ({})""".format(
        id_item,
        ", ".join([str(f) for f in config["playout_channels"].keys()])
        ))
    try:
        id_object, start, id_channel, meta = db.fetchall()[0]
    except IndexError:
        return False
    return Event(meta=meta)


def get_item_runs(id_channel, from_ts, to_ts, db=False):
    db = db or DB()
    db.query("SELECT id_item, start, stop FROM nx_asrun WHERE start >= %s and start < %s ORDER BY start ASC", [int(from_ts), int(to_ts)] )
    result = {}
    for id_item, start, stop in db.fetchall():
        result[id_item] = (start, stop)
    return result


def get_next_item(id_item, **kwargs):
    if not id_item:
        return False
    db = kwargs.get("db", DB())
    lcache = kwargs.get("cache", cache)

    logging.debug("Looking for item following item ID {}".format(id_item))
    current_item = Item(id_item, db=db, cache=lcache)
    current_bin = Bin(current_item["id_bin"], db=db, cache=lcache)
    for item in current_bin.items:
        if item["position"] > current_item["position"]:
            if item["item_role"] == "lead_out":
                logging.info("Cueing Lead In")
                for i, r in enumerate(current_bin.items):
                    if r["item_role"] == "lead_in":
                        return r
                else:
                    return current_bin.items[0]
            return item
    else:
        current_event = get_item_event(id_item, db=db, cache=lcache)
        db.query(
                "SELECT id_object, meta FROM nx_events WHERE id_channel = %s AND start > %s ORDER BY start ASC LIMIT 1",
                [current_event["id_channel"], current_event["start"]]
            )
        try:
            id_next_event, meta = db.fetchall()[0]
        except IndexError:
            logging.info("Looping current playlist (no more events scheduled)")
            return current_bin.items[0]

        next_event = Event(meta=meta)
        if not next_event.bin.items:
            logging.info("Looping current playlist (next event is empty)")
            return current_bin.items[0]

        if next_event["run_mode"]:
            logging.info("Looping current playlist (because of run_mode)")
            return current_bin.items[0]

        return next_event.bin.items[0]
