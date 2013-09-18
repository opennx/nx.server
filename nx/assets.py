#!/usr/bin/env python
# -*- coding: utf-8 -*-


from common import *
from time import *
import os



class Asset():
 def __init__(self,id_asset=False):
  if id_asset == -1:
   self.__new()
   self.status      = ONLINE
   self.asset_type  = VIDEO
   self.subtype     = VIRTUAL
   self.meta        = {"Title":"LIVE"}
  
  elif  id_asset: self.__load(id_asset)
  else:           self.__new()
 
 def __new(self):
  self.id_asset = False
  self.ctime = self.mtime = time()
  self.meta = {"Title":"Unsaved asset"}
  self.status     = CREATING
  self.asset_type = VIDEO
  self.subtype    = FILE
  self.parent     = 0
  self.spinoff    = 0
  self.folder     = 0
 
 
 def __load(self, id_asset, force_db=False):
  assetdata = []
  force_cache_save = False
  
  if not force_db:
   try:
    cached_data = json.loads(cache.load("A%s"%id_asset))
    self.id_asset, self.asset_type, self.parent, self.subtype, self.ctime, self.mtime, self.spinoff, self.status, self.folder = cached_data[0]
    self.meta = cached_data[1]
   except:
    force_db = True

   
  if force_db:
   logging.debug ("Loading asset %s from DB" % id_asset)
   db.query("SELECT id_asset, asset_type, parent, subtype, ctime, mtime, spinoff, status, id_folder FROM nebula_assets WHERE id_asset = %s"%id_asset)
   try:     assetdata = db.fetchall()[0]
   except:  return False
   
   self.id_asset, self.asset_type, self.parent, self.subtype, self.ctime, self.mtime, self.spinoff, self.status, self.folder = assetdata 
   self.meta = {}
   db.query("SELECT tag,value FROM nebula_meta WHERE id_asset = %s"%id_asset)
   for r in db.fetchall(): self.meta[r[0]] = r[1]
   force_cache_save = True
  
  if force_cache_save: self.__saveToCache()
  return True
  
 
 

 def dump(self):
  return [[self.id_asset, self.asset_type, self.parent, self.subtype, self.ctime, self.mtime, self.spinoff, self.status, self.folder], self.meta]
 
 def json(self):
  return json.dumps(self.dump())
  
 def filePath(self):
  return #TODO
 
 def duration(self):
  """returns "final" duration of the asset (after mark-in and mark-out) in seconds"""
  return 0 #TODO
 
 
 
 def save(self):
  if self.__saveToCache():
   db.commit()
  else:
   db.rollback()
   CriticalError("Unable to save %s to cache. This should never happen. Exiting" % self)

 
 def trash(self):
  pass #TODO
 
 def untrash(self):
  pass #TODO
  
 def purge(self):
  pass #TODO
  
 def __saveToCache(self):
  if self.id_asset:
   for i in range(4):
    if cache.save("A%s"%self.id_asset,self.json()): break
    sleep(.2)
   else:
    return False
  return True
    
 def __getitem__(self,key):
  if   key == "ctime"     : return self.ctime
  elif key == "mtime"     : return self.mtime
  elif key == "folder"    : return self.folder
  elif key == "status"    : return self.status 
  elif key == "asset_type": return self.asset_type
  elif key == "subtype"   : return self.subtype
  elif key == "parent"    : return self.parent
  elif key == "spinoff"   : return self.spinoff
  else: return self.meta.get(key,"")
  
 def __setitem__(self,key,value):
  if   key in ["ctime","Created"]     : self.ctime = int(value)
  elif key in ["mtime","Modified"]    : self.mtime = int(value)
  elif key in ["folder","Folder"]     : self.folder = int(value)
  elif key in ["status","Status"]     : 
   if value in [ONLINE, OFFLINE, CREATING, TRASHED, RESET]: self.status = value 
  elif key in ["asset_type","Asset type"]: 
   if value in [VIDEO,AUDIO,IMAGE,XML]:
    self.asset_type = value
  elif key.lower() == "subtype":
   if value in [FILE,COMPOSITE,VIRTUAL]: self.subtype = value
  elif key.lower() == "parent"               : self.parent  = int(value)
  elif key.lower() == "spinoff"              : self.spinoff = int(value)
  else: self.meta[key] = value
 
 def __repr__(self):
  try:
   return "Asset ID:%s (%s, %s)"%(self.id_asset,self["Title"].decode("utf-8"),self["Origin"])
  except:
   return "Asset ID:%s"%(self.id_asset)






def AssetByPath(storage, path):
 db.query("SELECT id_asset FROM nebula_meta WHERE tag='STORAGE' AND value='%s' AND id_asset IN (SELECT id_asset FROM nebula_meta WHERE tag='PATH' and value='%s')"%(storage,path))
 try:    return db.fetchall()[0][0]
 except: return False
  
def Browse():
 pass #TODO
 
def MetaExists(tag,value):
 db = dbconn()
 db.query("SELECT a.id_asset FROM nebula_meta as m, nebula_assets as a WHERE a.status <> 'TRASHED' AND a.id_asset = m.id_asset AND m.tag='%s' AND m.value='%s'"%(tag,value))
 res = db.fetchall()
 if res: return True
 return False

