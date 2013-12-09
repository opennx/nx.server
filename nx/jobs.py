#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Job():
 def __init__(self, service, agent_type, limit=False):
  self.service = service
 
  if limit: limit = "AND %s"%limit
  else:     limit=""
 
  id_asset = False
  settings = False
  id_state = False
  retries  = 0
 
  db = dbconn()
  db.query("SELECT ast.id_asset,ast.id_state,s.settings,ast.retries FROM nebula_asset_states as ast, nebula_states as s WHERE ast.id_state=s.id_state AND ( (ast.id_service = 0 AND ast.progress = 0) OR (ast.progress = -2 AND ast.retries < 2) ) AND s.agent_type = '%s' %s ORDER BY ast.id_asset DESC LIMIT 1" % (agent_type,limit))
  try:
   id_asset,id_state,settings,retries = db.fetchall()[0]
  except:
   pass
  else:
   db.query("UPDATE nebula_asset_states SET id_service = %s, reason='Job in progress' WHERE id_asset=%s AND id_state=%s"%(service.id_service,id_asset,id_state))
   db.commit()
   sleep(random.random()) # TODO: pokud tohle nezabrani tomu, aby se spustily dva stejny joby naraz, tak zrusit
   db.query("SELECT id_service FROM nebula_asset_states WHERE id_asset=%s AND id_state=%s"%(id_asset,id_state))

   r = db.fetchall()[0][0]
   if str(r) != str(service.id_service):
    service.logging.info("Giving up job %s/%s. Other service is working on it."%(id_asset, id_state))
    id_asset = False
    settings = False
    id_state = False
    retries  = 0

  self.id_asset = id_asset
  self.settings = settings
  self.id_state = id_state
  self.retries  = retries



 def SetProgress(self,PP,reason='Job in progress',retries=False):
  db = dbconn()
  db.query("SELECT progress FROM nebula_asset_states WHERE id_asset = %s AND id_state = %s" % (self.id_asset,self.id_state))
  try:    res = db.fetchall()[0][0]
  except: res = 0
  
  if   PP == -2: self.service.logging.error("Job (%d-%d) failed: %s"%(self.id_asset,self.id_state,reason))
  elif PP == -3: 
   self.service.logging.warning("Restarting job (%d-%d)"%(self.id_asset,self.id_state))
   res = -3
  elif PP == -4: 
   self.service.logging.warning("Aborting job (%d-%d)"%(self.id_asset,self.id_state))
   res = -4
  
  if not retries: retries = self.retries
  
  db.query("UPDATE nebula_asset_states set progress=%s, reason='%s',retries=%s  WHERE id_asset = %s and id_state = %s" %(PP,reason,retries,self.id_asset,self.id_state))
  db.commit()
  
  return res

