from nx import *

def api_get(**kwargs):
    start_time = time.time()

    db = kwargs.get("db", DB())
    conds = kwargs.get("conds", [])
    object_type = kwargs.get("object_type", "asset")
    result_type = kwargs.get("result", False)

    ObjectType, table = {
                "asset" : [Asset, "nx_assets"],
                "item" : [Item, "nx_items"],
                "bin" : [Bin, "nx_bins"],
                "event" : [Event, "nx_events"],
                "user" : [User, "nx_users"]
            }[object_type]

    result = {
            "data" : []
        }

    if kwargs.get("ids", []):
        result["data"] = [ObjectType(id, db=db) for id in kwargs.get["ids"]]
        result["count"] = len(result["data"])

    else:
        # Filtered results

        fulltext = kwargs.get("fulltext", False)
        if fulltext:
            ft = slugify(fulltext, make_set=True)
            conds.extend(["ft_index LIKE '%{}%'".format(elm) for elm in ft])

        conds = " AND ".join(conds)
        if conds:
            conds = "WHERE " + conds

        if kwargs.get("count", False):
            q = "SELECT count(id_object) FROM {} {}".format(table, conds)
            db.query(q)
            result["count"] = db.fetchall()[0][0]

        q = "SELECT id_object, meta FROM {} {}".format(table, conds)
        if "limit" in kwargs:
            q += " LIMIT {}".format(kwargs["limit"])

        logging.debug("Executing get query:", q)
        db.query(q)

        if result_type == "ids":
            for id_object, meta in db.fetchall():
                result["data"].append(id_object)

        elif type(result_type) == list:
            for id_object, meta in db.fetchall():
                if meta:
                    obj = ObjectType(meta=meta, db=db)
                else:
                    obj = ObjectType(id_object, db=db)
                result["data"].append([obj[key] for key in result_type])

        else:
            for id_object, meta in db.fetchall():
                if meta:
                    result["data"].append(ObjectType(meta=meta, db=db).meta)
                else:
                    result["data"].append(ObjectType(id_object, db=db).meta)

    #
    # response
    #

    result["response"] = 200
    result["message"] = "{} {}s returned in {:.02}s".format(
            len(result["data"]),
            object_type,
            time.time() - start_time
        )
    return result
