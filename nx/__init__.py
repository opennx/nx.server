from .core import *
from .connection import *
from .objects import *
from .helpers import *
from .api import *

#
# Load system configuration
#

def load_site_settings(db, force=False):
    global config
    site_settings = {
               "playout_channels" : {},
               "ingest_channels" : {},
               "views" : {},
               "asset_types" : {}
            }

    # Settings

    db.query("SELECT key, value FROM nx_settings")
    for key, value in db.fetchall():
        site_settings[key] = value

    # Views

    db.query("SELECT id_view, config FROM nx_views")
    for id, settings in db.fetchall():
        settings = xml(settings)
        view = {}
        for elm in ["query", "folders", "origins", "media_types", "content_types", "statuses"]:
            try:
                view[elm] = settings.find(elm).text.strip()
            except:
                continue
        site_settings["views"][id] = view

    # Channels

    db.query("SELECT id_channel, channel_type, title, config FROM nx_channels")
    for id_channel, channel_type, title, ch_config in db.fetchall():
        try:
            ch_config = json.loads(ch_config)
        except:
            print ("Unable to parse channel {}:{} config.".format(id_channel, title))
            continue
        ch_config.update({"title":title})
        if channel_type == PLAYOUT:
            site_settings["playout_channels"][id_channel] = ch_config
        elif channel_type == INGEST:
            site_settings["ingest_channels"][id_channel] = ch_config
    config.update(site_settings)
    return True



def load_storages(db, force=False):
    global storages
    db.query("SELECT id_storage, title, protocol, path, login, password FROM nx_storages")
    for id_storage, title, protocol, path, login, password in db.fetchall():
        storage = Storage(
            id=id_storage,
            title=title,
            protocol=protocol,
            path=path,
            login=login,
            password=password
            )
        storages.add(storage)
    return True

#
# Load metadata model
#

def load_meta_types(db, force=False):
    global meta_types
    db.query("SELECT namespace, tag, editable, searchable, class, default_value,  settings FROM nx_meta_types")
    for ns, tag, editable, searchable, class_, default, settings in db.fetchall():
        meta_type = MetaType(tag)
        meta_type.namespace  = ns
        meta_type.editable   = bool(editable)
        meta_type.searchable = bool(searchable)
        meta_type.class_     = class_
        meta_type.default    = default
        meta_type.settings   = json.loads(settings)
        db.query("SELECT lang, alias, col_header FROM nx_meta_aliases WHERE tag='{0}'".format(tag))
        for lang, alias, col_header in db.fetchall():
            meta_type.aliases[lang] = alias, col_header
        meta_types[tag] = meta_type
    return True


def load_cs(db, force=False):
    pass

#
# Do it! Do it! Do it!
#

def load_all_settings(force=False):
    logging.debug("Loading site configuration from DB", handlers=False)
    try:
        # This is the first time we are connecting DB so error handling should be here
        db = DB()
    except:
        log_traceback(handlers=False)
        critical_error("Unable to connect database", handlers=False)

    load_site_settings(db, force)
    load_storages(db, force)
    load_meta_types(db, force)
    load_cs(db, force)

    messaging.configure()
    cache.configure()

load_all_settings()
