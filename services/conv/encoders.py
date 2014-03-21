from nx import *
from nx.assets import *

from nx.common.metadata import meta_types
from nx.common.filetypes import file_types

import uuid
import stat
import subprocess

class Encoder():
    def __init__(self, asset, task, vars):
        self.asset = asset
        self.task = task
        self.vars = vars
        self.proc = None

    def configure(self):
        pass

    def run(self):
        pass

    def is_working(self):
        return False

    def get_progress(self): 
        """Should return float between 0.0 and 1.0"""
        return 0

    def finalize(self):
        pass



def temp_file(id_storage, ext):
    if id_storage:
        temp_path = os.path.join(storages[id_storage].get_path(),".nx", "creating")
    else:
        temp_path = "/tmp/nx"

    if not os.path.exists(temp_path):
        try:
            os.makedirs(temp_path)
        except: 
            return False

    temp_name = str(uuid.uuid1()) + ext
    return os.path.join(temp_path, temp_name)


## ENCODERS COMMON
#########################################################################
## FFMPEG

class FFMPEG(Encoder):
    def configure(self):
        self.ffparams = ["ffmpeg", "-y"]
        self.ffparams.extend(["-i", self.asset.get_file_path()])
        asset = self.asset

        ########################
        ## Output path madness

        #try:
        id_storage = int(self.task.find("storage").text)
        self.id_storage = id_storage
        self.target_rel_path = eval(self.task.find("path").text)
        #except:
        #    return "Wrong target script"

        if not storages[id_storage]:
            return "Target storage is not mounted"


        temp_ext  = os.path.splitext(self.target_rel_path)[1]
        self.temp_file_path   = temp_file(id_storage, temp_ext)
        if not self.temp_file_path:
            return "Unable to create temp directory"

        self.target_file_path = os.path.join(storages[id_storage].get_path(), self.target_rel_path)
        self.target_dir_path  = os.path.split(self.target_file_path)[0]

        if not (os.path.exists(self.target_dir_path) and stat.S_ISDIR(os.stat(self.target_dir_path)[stat.ST_MODE])):
            try:    
                os.makedirs(self.target_dir_path)
            except: 
                return "Unable to create output directory"

        ## Output path madness
        ########################

        for param in self.task.findall("param"):
            value = eval(param.text)
            self.ffparams.extend(["-{}".format(param.attrib["name"]), value])

        self.ffparams.append(self.temp_file_path)

        return False # no error



    def run(self):
        logging.debug("Executing {}".format(str(self.ffparams)))
        self.proc = subprocess.Popen(self.ffparams)

    def is_working(self):
        if not self.proc or self.proc.poll() == None:
            return True
        return False

    def get_progress(self):
        if not self.proc:
            return 0
        elif self.proc.poll() == 0:
            return COMPLETED
        elif self.proc.poll() > 0:
            return FAILED
        else:
            return 0.5



    def finalize(self):
        new = None
        asset = self.asset

        if self.task.find("target").text == "new":    
            id_storage = self.id_storage
            r = asset_by_path(id_storage, self.target_rel_path)
            if r:     
                new = Asset(r)
                logging.info("Updating asset {!r}".format(new))
            else:
                logging.info("Creating new asset for {!r} conversion.".format(asset))
                new = Asset()
                new["media_type"]   = FILE
                new["content_type"] = VIDEO
                
                new["version_of"]   = asset.id
                new["id_storage"]   = id_storage
                new["path"]         = self.target_rel_path
                new["origin"]       = "Video conversion"
                new["id_folder"]    = asset["id_folder"]

                for key in asset.meta:
                    if key in meta_types and meta_types[key].namespace in ["AIEB", "m"]:
                        new[key] = asset[key]
            
            new["status"] = CREATING



        for intra in self.task.findall("intra"):
            exec(intra.text)

        try:
            os.rename(self.temp_file_path, self.target_file_path)
        except:
            return "Unable to move output file to target destination"
   
        if new is not None:
            new.save()

        for post in self.task.findall("post"):
            exec(post.text)

        if new is not None:
            new.save()
        asset.save()


## FFMPEG
#########################################################################