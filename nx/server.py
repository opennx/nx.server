#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import *

########################################################################
## Database

if config['db_driver'] == 'postgres': 
    import psycopg2
    class DB():
        def __init__(self):
            self._connect()

        def _connect(self):  
            self.conn = psycopg2.connect(database = config['db_name'], 
                                         host     = config['db_host'], 
                                         user     = config['db_user'],
                                         password = config['db_pass']
                                         ) 
            self.cur = self.conn.cursor()

        def query(self,q,*args):
            self.cur.execute(q,*args)

        def sanit(self, instr):
            #TODO: THIS SHOULD BE HEEEEAAAVILY MODIFIED
            try: return str(instr).replace("''","'").replace("'","''").decode("utf-8")
            except: return instr.replace("''","'").replace("'","''")

        def fetchall(self):
            return self.cur.fetchall()
       
        def lastid (self):
            self.query("select lastval()")
            return self.fetchall()[0][0]

        def commit(self):
            self.conn.commit()

        def rollback(self):
            self.conn.rollback()


elif config['db_driver'] == 'sqlite':
    import sqlite3
    class DB():
        def __init__(self):
            self._connect()

        def _connect(self):
            try:
                self.conn = sqlite3.connect(config["db_host"]) 
                self.cur = self.conn.cursor()
            except:
                raise Exception, "Unable to connect database."

        def query(self,q,*args):
            self.cur.execute(q,*args)

        def sanit(self, instr):
            try: return str(instr).replace("''","'").replace("'","''").decode("utf-8")
            except: return instr.replace("''","'").replace("'","''")

        def fetchall(self):
            return self.cur.fetchall()
          
        def lastid(self):
            r = self.cur.lastrowid
            return r
          
        def commit(self):
            self.conn.commit()

        def rollback(self):
            self.conn.rollback()
         
        def close(self):
            self.conn.close()

else:
    critical_error("Unknown DB Driver. Exiting.")
 
## Database
#######################################################################################################
## Site settings

def load_site_settings():
    """Should be called after db initialisation"""
    try:
        db = DB()
        db.query("SELECT key, value FROM nx_settings")
        for key, value in db.fetchall():
            config[key] = value
    except:
        print "Unable to load local settings. Nothing will work."

load_site_settings()
messaging.init()

## Site settings
#######################################################################################################
## Cache


if config["cache_driver"] == "memcached":
    import pylibmc

    class Cache():
        def __init__(self):
            self.site = config["site_name"]
            self.host = config["cache_host"]
            self.port = config["cache_port"]
            self.cstring = '%s:%s'%(self.host,self.port)

        def _conn(self):
            return pylibmc.Client([self.cstring])

        def load(self,key):
            try:
                conn = self._conn()
                return conn.get("%s_%s"%(self.site,key))
            except:
                return False

        def save(self,key,value):
            for i in range(10):
                try:
                    conn = self._conn()
                    val = conn.set("%s_%s"%(self.site,key),value)
                    break
                except:  
                    print "MEMCACHE SAVE FAILED %s" % key
                    print str(sys.exc_info())
                    time.sleep(1)
                else:
                    critical_error ("Memcache save failed. This should never happen. Check MC server")
                    sys.exit(-1)
            return val

        def delete(self,key):
            for i in range(10):
                try:
                    conn = self._conn()
                    conn.delete("%s_%s"%(self.site,key))
                    break
                except: 
                    print "MEMCACHE DELETE FAILED %s" % key
                    print str(sys.exc_info())
                    time.sleep(1)
                else:
                    critical_error ("Memcache delete failed. This should never happen. Check MC server")
                    sys.exit(-1)
            return True


else:
    class Cache():
        def __init__(self):
            self.cachename = ".cache"
        def load(self,key):
            try:
                return json.loads(open(self.cachename).read())[key]
            except:
                return False

        def save(self,key,value):
            if os.path.exists(self.cachename):
                data = json.loads(open(self.cachename).read())
            else:
                data = {}
            data[key] = value
            f = open(self.cachename,"w")
            f.write(json.dumps(data))
            f.close()
            return True

cache     = Cache()

## Cache
########################################################################
## Storages

class Storage():
    def __init__(self): 
        pass

    def get_path(self,rel=False):
        if self.protocol == LOCAL:
            return self.path

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
