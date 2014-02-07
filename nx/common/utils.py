#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import os
import time
import unicodedata




def unaccent(instr,encoding="utf-8"):
    return unicodedata.normalize('NFKD', instr).encode('ascii', 'ignore')

## String manipulation
######################################################################## 
## Time formating

def datestr2ts(datestr, hh=0, mm=0, ss=0):
    yy,mo,dd = [int(i) for i in datestr.split("-")]
    return int(time.mktime(time.struct_time([yy,mo,dd,hh,mm,ss,False,False,False])))


def s2time(secs):
    """Converts seconds to time"""
    try:
        secs = float(secs)
    except:
        return "--:--:--.--"
    wholesecs = int(secs)
    milisecs = int((secs - wholesecs) * 100)
    hh = wholesecs / 3600
    hd = hh % 24
    mm = (wholesecs / 60) - (hh*60)
    ss = wholesecs - (hh*3600) - (mm*60)
    return "{:02d}:{:02d}:{:02d}.{:02d}".format(hd, mm, ss, milisecs) 


def f2tc(f,base=25):
    """Converts frames to timecode"""
    try:
        f = int(f)
    except:
        return "--:--:--.--"
    hh = int((f / base) / 3600)
    mm = int(((f / base) / 60) - (hh*60))
    ss = int((f/base) - (hh*3600) - (mm*60))
    ff = int(f - (hh*3600*base) - (mm*60*base) - (ss*base))
    return "{:02d}:{:02d}:{:02d}:{:02d}".format(hh, mm, ss, ff) 
 
 
def s2tc(s,base=25):
    """Converts seconds to timecode"""
    try:    f = int(s*base)
    except: return "--:--:--:--"
    hh  = int((f / base) / 3600)
    hhd = int((hh%24))
    mm  = int(((f / base) / 60) - (hh*60))
    ss  = int((f/base) - (hh*3600) - (mm*60))
    ff  = int(f - (hh*3600*base) - (mm*60*base) - (ss*base))
    return "{:02d}:{:02d}:{:02d}:{:02d}".format(hhd, mm, ss, ff) 
 
 
def s2words(s):
    s = int(s)
    if   s < 60:   return "{} seconds".format(s)
    elif s < 120:  return "1 min {} secs".format(s-60)
    elif s < 7200: return "{} minutes".format(round(s/60))
    else:          return "{} hours".format(round(s/3600))


## Time formating
########################################################################
 
 
def file_has_sibling(path,exts=[]):
    """ Tests if the file has a sibling (file with same basename in the same folder, but with different extension."""
    root = os.path.splitext(path)[0]
    for f in exts:
        tstf = root+"."+f
        if os.path.exists(tstf):
            return tstf
    return False
