from nx import *


__all__ = [
        "api_get",       # list objects
        "api_create",    # create new object(s)
        "api_update",    # update object(s) metadata

#        "api_actions",
#        "api_send",

#        "api_order",     # create / reorder bin items
#        "api_remove",    # remove item from bin

#        "api_schedule",  # set events
#        "api_runs",  # get list of timestamps when asset is scheduled
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
    db = kwargs.get("db", DB())
    conds = []

    fulltext = kwargs.get("fulltext", False)
    if fulltext:
        ft = slugify(fulltext, make_set=True)
        conds.extend(["ft_index LIKE '%{}%'".format(elm) for elm in ft])

    conds = " AND ".join(conds)
    if conds:
        conds = "WHERE " + conds
    q = "SELECT meta FROM nx_assets {}".format(conds)
    if "limit" in kwargs:
        q += " LIMIT {}".format(kwargs["limit"])
    logging.debug("Executing browse query:", q)
    db.query(q)
    for meta, in db.fetchall():
        yield Asset(meta=meta, db=db)

def api_create(**kwargs):
    pass


def api_update(**kwargs):
    pass


