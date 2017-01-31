from .core import *
from .connection import *
from .objects import *
from .helpers import *
from .api import *
from .plugins import *

#
# Load system configuration
#

def load_site_settings(db, force=False):
    global config

    config["playout_channels"] = {}
    config["ingest_channels"] = {}
    config["views"] = {}
    config["asset_types"] = {}
    config["folders"] = {}

    # Settings

    db.query("SELECT key, value FROM nx_settings")
    for key, value in db.fetchall():
        config[key] = value

    # Views

    db.query("SELECT id_view, title, position, config FROM nx_views")
    for id, title, position, settings in db.fetchall():
        settings = xml(settings)
        view = {"name" : title, "columns" : [], "position" : position}
        columns = settings.find("columns")
        if columns is not None:
            for column in columns.findall("column"):
                if column.text:
                    view["columns"].append(column.text.strip())
        for elm in ["query", "folders", "origins", "media_types", "content_types", "statuses"]:
            try:
                view[elm] = settings.find(elm).text.strip()
            except Exception:
                continue
        config["views"][id] = view

    # Channels

    db.query("SELECT id_channel, channel_type, title, config FROM nx_channels")
    for id_channel, channel_type, title, ch_config in db.fetchall():
        try:
            ch_config = json.loads(ch_config)
        except Exception:
            logging.error("Unable to parse channel {}:{} config.".format(id_channel, title))
            continue
        ch_config.update({"title":title})
        if channel_type == PLAYOUT:
            config["playout_channels"][id_channel] = ch_config
        elif channel_type == INGEST:
            config["ingest_channels"][id_channel] = ch_config

    # Folders

    db.query("SELECT id_folder, title, color, meta_set, validator FROM nx_folders")
    for id_folder, title, color, meta_set, validator in db.fetchall():
        config["folders"][id_folder] = {
                "title" : title,
                "color" : color,
                "meta_set" : json.loads(meta_set),
                "validator" : validator
            }


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
        meta_type = MetaType(
                tag, **{
                    "namespace" : ns,
                    "editable" : bool(editable),
                    "searchable" : bool(searchable),
                    "class" : class_,
                    "default" : default,
                    "settings" : json.loads(settings)
                }
            )
        db.query("SELECT lang, alias, col_header FROM nx_meta_aliases WHERE tag='{0}'".format(tag))
        for lang, alias, col_header in db.fetchall():
            meta_type["aliases"][lang] = alias, col_header or alias
        meta_types[tag] = meta_type
    return True


def load_cs(db, force=False):
    pass

#
# Put it together
#

def load_all_settings(force=False):
    logging.debug("Loading site configuration from DB", handlers=False)
    try:
        # This is the first time we are connecting DB so error handling should be here
        db = DB()
    except Exception:
        log_traceback(handlers=False)
        critical_error("Unable to connect database", handlers=False)

    load_site_settings(db, force)
    load_storages(db, force)
    load_meta_types(db, force)
    load_cs(db, force)

    messaging.configure()
    cache.configure()

#
# Do it! Do it! Do it!
#

load_all_settings()

if plugin_path:
    python_plugin_path = os.path.join(plugin_path, "python")
    if os.path.exists(python_plugin_path):
        sys.path.append(python_plugin_path)
