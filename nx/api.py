__all__ = [
        "api_get",       # list objects
        "api_create",    # create new object(s)
        "api_update",    # update object(s) metadata

        "api_actions",
        "api_send",

        "api_order",     # create / reorder bin items
        "api_remove",    # remove item from bin

        "api_schedule",  # set events
        "api_runs",  # get list of timestamps when asset is scheduled
    ]



"""
message

services
meta_types
site_settings

get_assets
get_objects
get_events
rundown
set_events
"""


def api_get(**kwargs):
    db = DB()
    conds = []

    for key in kwargs:
        value = kwargs[key]
        if type(value) == list:
            operator = "IN"
            value = "({})".format(", ".join("'{}'".format(value) for value in value))
        else:
            operator = "="
            value = "'{}'".format(value)
        conds.append("meta->>'{}' {} {}".format(key, operator, value))

    if fulltext:
        ft = slugify(fulltext, make_set=True)
        conds.extend(["ft_index LIKE '%{}%'".format(elm) for elm in ft])

    conds = " AND ".join(conds)
    if conds:
        conds = "WHERE " + conds
    q = "SELECT meta FROM nx_assets {}".format(conds)
    logging.debug("Executing browse query:", q)
    db.query(q)
    for meta, in db.fetchall():
        yield Asset(meta=meta)

def api_create(**kwargs):
    pass


def api_update(**kwargs):
    pass


