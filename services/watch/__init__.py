#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx import *
from nx.assets import *

from stat import *
from filetypes import FILETYPES

def get_files(basepath,recursive=False,hidden=False):
    if os.path.exists(basepath):
        for filename in os.listdir(basepath):
            if not hidden and filename.startswith("."):
                continue
            filepath = os.path.join(basepath,filename) 
            if S_ISREG(os.stat(filepath)[ST_MODE]): 
                yield filepath
            if S_ISDIR(os.stat(filepath)[ST_MODE]) and recursive: 
                for f in get_files(filepath,recursive=recursive,hidden=hidden): yield f

def file_to_title(fname):
    return os.path.basename(os.path.splitext(fname)[0]).replace("_"," ")

class Service(ServicePrototype):
    def onInit(self):
        self.mirrors = self.settings.findall("mirror")

    def onMain(self):
        db = DB()

        for mirror in self.mirrors:
            ###################
            ## Mirror settings

            mstorage = int(mirror.find("id_storage").text)
            mpath    = mirror.find("path").text
            stpath   = storages[mstorage].get_path()
           

            filters = []
            try:    filters = mirror.find("filters").findall("filter")
            except: filtered = True
            else:   filtered = False


            try:    mrecursive = int(mirror.find("recursive").text)
            except: mrecursive = 0

            try:    mhidden = int(mirror.find("hidden").text)
            except: mhidden = 0

            ## Mirror settings
            ###################


            for f in get_files(os.path.join(stpath,mpath),recursive=mrecursive,hidden=mhidden):

                apath = os.path.normpath(f.replace(stpath,""))
                apath = apath.lstrip("/")  
                if apath == "": continue 
         
                try:    filetype = FILETYPES[os.path.splitext(f)[1][1:].lower()]
                except: continue
   
            
                if asset_by_path(mstorage,apath,db=db): continue 

                asset = Asset() 
                asset["id_storage"]    = mstorage
                asset["path"]          = apath
                asset["title"]         = file_to_title(apath)
                asset["content_type"]  = filetype
                asset["media_type"]    = FILE
                asset["status"]        = CREATING

                for mt in mirror.findall("meta"):
                  try:
                   if mt.attrib["type"] == "script":
                    exec "asset[mt.attrib[\"tag\"]] = %s"% (mt.text or "")
                   else: raise Exception
                  except:
                   asset[mt.attrib["tag"]] = mt.text or ""
               
           
                try:
                  killoffset = int(mirror.find("kill_offset").text)
                  asset.SetMeta("Kill date", str(int(time())+killoffset))
                except:
                  pass
                
                failed = False
                for post_script in mirror.findall("post"):
                  try:
                   exec(post_script.text)
                  except:
                   self.logging.error("Error executing post-script \"%s\" on %s" % (post_script.text, asset))
                   self.logging.error(str(sys.exc_info()))
                   failed = True
             
                if not failed:
                    asset.save()
                    logging.info("Created new %s from %s"%(asset, apath))