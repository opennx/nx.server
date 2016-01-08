from .core import *

connection_type = "server"

__all__ = ["connection_type", "DB", "cache", "Cache"]

#######################################################################################################
## Database

class DBproto(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self._connect()

    def _connect(self):
        pass

    def query(self, q, *args):
        self.cur.execute(q,*args)

    def fetchall(self):
        return self.cur.fetchall()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def __len__(self):
        return True

if config['db_driver'] == 'postgres':
    import psycopg2
    class DB(DBproto):
        def _connect(self):
            i = 0
            while i < 3:
                try:
                    self.conn = psycopg2.connect(database = self.kwargs.get('db_name', False) or config['db_name'],
                                                 host     = self.kwargs.get('db_host', False) or config['db_host'],
                                                 user     = self.kwargs.get('db_user', False) or config['db_user'],
                                                 password = self.kwargs.get('db_pass', False) or config['db_pass']
                                                 )
                except psycopg2.OperationalError:
                    time.sleep(1)
                    i+=1
                    continue
                else:
                    break

            self.cur = self.conn.cursor()

        def sanit(self, instr):
            try:
                return str(instr).replace("''","'").replace("'","''").decode("utf-8")
            except:
                return instr.replace("''","'").replace("'","''")

        def lastid (self):
            self.query("select lastval()")
            return self.fetchall()[0][0]

elif config['db_driver'] == 'sqlite':
    import sqlite3
    class DB(DBproto):
        def _connect(self):
            try:
                self.conn = sqlite3.connect(config["db_host"])
                self.cur = self.conn.cursor()
            except:
                raise (Exception, "Unable to connect database.")

        def sanit(self, instr):
            try:
                return str(instr).replace("''","'").replace("'","''").decode("utf-8")
            except:
                return instr.replace("''","'").replace("'","''")

        def lastid(self):
            r = self.cur.lastrowid
            return r

else:
    critical_error("Unknown DB Driver. Exiting.")

## Database
#######################################################################################################
## Site settings

def load_site_settings():
    """Should be called after db initialisation"""
    db = DB()
    global config

    config["playout_channels"] = {}
    config["ingest_channels"] = {}
    config["views"] = {}

    db.query("SELECT key, value FROM nx_settings")
    for key, value in db.fetchall():
        config[key] = value

    db.query("SELECT id_view, config FROM nx_views")
    for id_view, view_config in db.fetchall():
        view_config = ET.XML(view_config)
        view = {}
        for elm in ["query", "folders", "origins", "media_types", "content_types", "statuses"]:
            try:
                view[elm] = view_config.find(elm).text.strip()
            except:
                continue
        config["views"][id_view] = view

    db.query("SELECT id_channel, channel_type, title, config FROM nx_channels")
    for id_channel, channel_type, title, ch_config in db.fetchall():
        try:
            ch_config = json.loads(ch_config)
        except:
            print ("Unable to parse channel {}:{} config.".format(id_channel, title))
            continue
        ch_config.update({"title":title})
        if channel_type == PLAYOUT:
            config["playout_channels"][id_channel] = ch_config
        elif channel_type == INGEST:
            config["ingest_channels"][id_channel] = ch_config




load_site_settings()
messaging.configure()

## Site settings
#######################################################################################################
## Cache

import pylibmc

class Cache():
    def __init__(self):
        self.site = config["site_name"]
        self.host = config["cache_host"]
        self.port = config["cache_port"]
        self.cstring = '%s:%s'%(self.host,self.port)
        self.pool = False
        self.connect()

    def connect(self):
        self.conn = pylibmc.Client([self.cstring])
        self.pool = False

    def load(self, key):
        if config.get("mc_thread_safe", False):
            return self.tload(key)

        key = "{}_{}".format(self.site,key)
        try:
            result = self.conn.get(key)
        except pylibmc.ConnectionError:
            self.connect()
            result = False
        return result

    def save(self, key, value):
        if config.get("mc_thread_safe", False):
            return self.tsave(key, value)

        key = "{}_{}".format(self.site, key)
        for i in range(10):
            try:
                self.conn.set(key, str(value))
                break
            except:
                logging.error("Cache save failed ({}): {}".format(key, str(sys.exc_info())))
                time.sleep(.3)
                self.connect()
        else:
            critical_error ("Memcache save failed. This should never happen. Check MC server")
            sys.exit(-1)
        return True

    def delete(self,key):
        if config.get("mc_thread_safe", False):
            return self.tdelete(key)
        key = "{}_{}".format(self.site, key)
        for i in range(10):
            try:
                self.conn.delete(key)
                break
            except:
                logging.error("Cache delete failed ({}): {}".format(key, str(sys.exc_info())))
                time.sleep(.3)
                self.connect()
        else:
            critical_error ("Memcache delete failed. This should never happen. Check MC server")
            sys.exit(-1)
        return True


    def tload(self, key):
        if not self.pool:
            self.pool = pylibmc.ThreadMappedPool(self.conn)
        key = "{}_{}".format(self.site, key)
        result = False
        with self.pool.reserve() as mc:
            try:
                result = mc.get(key)
            except pylibmc.ConnectionError:
                self.connect()
                result = False
        self.pool.relinquish()
        return result

    def tsave(self, key, value):
        if not self.pool:
            self.pool = pylibmc.ThreadMappedPool(self.conn)
        key = "{}_{}".format(self.site, key)
        with self.pool.reserve() as mc:
            for i in range(10):
                try:
                    mc.set(key, str(value))
                    break
                except:
                    logging.error("Cache save failed ({}): {}".format(key, str(sys.exc_info())))
                    time.sleep(.3)
                    self.connect()
            else:
                critical_error ("Memcache save failed. This should never happen. Check MC server")
                sys.exit(-1)
        self.pool.relinquish()
        return True

    def tdelete(self,key):
        if not self.pool:
            self.pool = pylibmc.ThreadMappedPool(self.conn)
        key = "{}_{}".format(self.site, key)
        with self.pool.reserve() as mc:
            for i in range(10):
                try:
                    mc.delete(key)
                    break
                except:
                    logging.error("Cache delete failed ({}): {}".format(key, str(sys.exc_info())))
                    time.sleep(.3)
                    self.connect()
            else:
                critical_error ("Memcache delete failed. This should never happen. Check MC server")
                sys.exit(-1)
        self.pool.relinquish()
        return True




cache = Cache()

## Cache
########################################################################
## Storages

class Storage():
    def __init__(self):
        pass

    @property
    def local_path(self):
        if self.protocol == LOCAL:
            return self.path
        elif PLATFORM == "windows":
            return ""
        else:
            return os.path.join ("/mnt","nx%02d"%self.id_storage)

    def get_path(self,rel=False):
        logging.warning("get_path is deprecated")
        return self.local_path

    def __len__(self):
        return ismount(self.local_path) and len(os.listdir(self.local_path)) != 0

def load_storages():
    try:
        db = DB()
        db.query("SELECT id_storage, title, protocol, path, login, password FROM nx_storages")
    except:
        return

    for id_storage, title, protocol, path, login, password in db.fetchall():
        storage = Storage()
        storage.id_storage = id_storage
        storage.title      = title
        storage.protocol   = protocol
        storage.path       = path
        storage.login      = login
        storage.password   = password
        storages[id_storage] = storage

load_storages()
