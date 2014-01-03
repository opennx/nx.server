#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from nx.constants import *
from nx.shell import shell

class Probe(object):
    title = "Generic Probe"
    def __init__(self):
        pass

    def __repr__(self):
        return self.title

    def accepts(self, asset):
        return False

    def work(self, asset):
        return asset

###############################################################################################

def ffprobe(fname):
    cmd = "ffprobe -i \"%s\" -show_streams -show_format -print_format json" % fname 
    proc = shell(cmd)
    return json.loads(proc.stdout().read())

def guess_aspect (w,h):
    if 0 in [w,h]: return ""
    valid_aspects = [(16, 9), (4, 3), (2.35, 1)]
    ratio = float(w) / float(h)
    return "%s:%s" % min(valid_aspects, key=lambda x:abs((float(x[0])/x[1])-ratio))

class FFProbe(Probe):
    title = "FFProbe"

    def accepts(self, asset):
        return asset["content_type"] in [VIDEO, AUDIO, IMAGE]

    def work(self, asset):
        old_meta = asset.meta
        fname = asset.get_file_path()
        dump = ffprobe(fname)

        streams = dump["streams"]
        format  = dump["format"]

        asset["format"]   = format.get("format_name", "")
        asset["duration"] = format.get("duration", "")

        ## Streams

        at_atrack  = 1         # Audio track identifier (A1, A2...)

        for stream in streams:
            if stream["codec_type"] == "video":

                asset["video/fps"]          = stream.get("r_frame_rate","")
                asset["video/codec"]        = stream.get("codec_name","")
                asset["video/pixel_format"] = stream.get("pix_fmt",   "")
              
                if not asset["duration"]:
                    dur = float(stream.get("duration",0))
                    if dur:
                        asset["duration"] = dur 
                    else:
                        if stream.get("nb_frames","FUCK").isnumeric(): 
                            if asset["video/fps"]:
                                asset["duration"] = int(stream["nb_frames"]) / asset[fps]
    
                ## Duration
                ####################
                ## Frame size
                   
                try: 
                    w, h = int(stream["width"]),int(stream["height"])
                except: 
                    pass
                else: 
                    if w and h:
                        asset["video/width"]  = w
                        asset["video/height"] = h
                    
                    if not (w and h):
                        pass
                    elif "video/aspect_ratio" in old_meta and old_meta.get("video/width",0) == w: 
                        pass # Pokud uz v meta aspect je a velikost se nezmenila, tak hodnotu neupdatujem. mohl ji zmenit uzivatel                     
                    else:
                        if stream.get("display_aspect_ratio",False) in ["4:3", "16:9"]:
                            asset["video/aspect_ratio"] = stream["display_aspect_ratio"]
                        else:
                            asset["video/aspect_ratio"] = guess_aspect(w, h)

            elif stream["codec_type"] == "audio":
                asset["audio/codec"] == stream

        ## Streams
        ######################
        ## TAGS

        if "tags" in format.keys() and not "meta_probed" in asset.meta:
            if content_type == AUDIO:
                tag_mapping = {
                                "title"   : "title",
                                "artist"  : "role/performer",
                                "composer": "role/composer",
                                "album"   : "album",
                              }
            else:
                tag_mapping = {
                                "title" : "title"
                                }

            for tag in format["tags"]:
                value = format["tags"][tag]
                if tag in tag_mapping:
                    if not tag_mapping[tag] in asset.meta or tag == "title": # Only title should be overwriten if exists. There is a reason
                        asset[tag_mapping[tag]] = value
                elif tag in ["track","disc"] and content_type == AUDIO:
                    if not "album/%s"%tag in asset.meta: 
                        asset["album/%s"%tag] = value.split("/")[0]
                elif tag == "genre" and content_type == AUDIO:
                    # Ultra mindfuck
                    from nx.cs import NX_MUSIC_GENRES

                    for genre in NX_MUSIC_GENRES:
                        genre_parts = genre.lower().split()
                        for g in genre_parts:
                            if value.lower().find(g) > -1:
                                continue
                            break
                        else:
                            if not "genre/music" in asset.meta:
                                asset["genre/music"] = genre
                            break
                    else:
                        if not "genre/music" in asset.meta:
                            asset["genre/music"] = value
            asset["meta_probed"] = 1

        ## TAGS
        ######################
        return asset


class YTProbe(Probe):
    pass

class VimeoProbe(Probe):
    pass

###############################################################################################

probes = [FFProbe()]
