from nx import *

#
# TODO:
# - list result type in ids select
#


def api_get(**kwargs):
    object_type = kwargs.get("object_type", "asset")
    ids         = kwargs.get("ids", [])
    conds       = kwargs.get("conds", [])
    fulltext    = kwargs.get("fulltext", False)
    result_type = kwargs.get("result", False)
    count       = kwargs.get("count", False)
    limit       = kwargs.get("limit", False)
    offset      = kwargs.get("offset", False)
    user        = kwargs.get("user", anonymous)
    db          = kwargs.get("db", DB())

    start_time = time.time()

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

    if ids:
        result["data"] = [ObjectType(id, db=db) for id in ids]
        result["count"] = len(result["data"])

    else:
        # Filtered results

        if fulltext:
            ft = slugify(fulltext, make_set=True)
            conds.extend(["ft_index LIKE '%{}%'".format(elm) for elm in ft])

        conds = " AND ".join(conds)
        if conds:
            conds = "WHERE " + conds

        if count:
            q = "SELECT count(id_object) FROM {} {}".format(table, conds)
            db.query(q)
            result["count"] = db.fetchall()[0][0]

        q = "SELECT id_object, meta FROM {} {}".format(table, conds)
        if limit:
            q += " LIMIT {}".format(limit)
        if offset:
            q += " OFFSET {}".format(offset)

        logging.debug("Executing get query:", q)
        db.query(q)

        if result_type == "ids":
            for id_object, meta in db.fetchall():
                result["data"].append(id_object)

        elif type(result_type) == list:
            result_format = []
            for i, key in enumerate(result_type):
                form = key.split("@")
                if len(form) == 2:
                    result_format.append(json.loads(form[1] or "{}"))
                else:
                    result_format.append(None)
                result_type[i] = form[0]

            for id_object, meta in db.fetchall():
                if meta:
                    obj = ObjectType(meta=meta, db=db)
                else:
                    obj = ObjectType(id_object, db=db)
                row = []
                for key, form in zip(result_type, result_format):
                    if form is None:
                        row.append(obj[key])
                    else:
                        form = form or {}
                        row.append(obj.show(key, **form))
                result["data"].append(row)

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
