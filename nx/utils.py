#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import os
import unicodedata

######################################################################## 
## Time formating


def unaccent(instr,encoding="utf-8"):
    #return unicodedata.normalize('NFKD', unicode(instr,encoding)).encode('ascii', 'ignore')
    return unicodedata.normalize('NFKD', instr).encode('ascii', 'ignore')

def s2time(secs):
    """Converts seconds to time"""
    try:
        secs = float(secs)
    except:
        return "--:--:--.--"
    wholesecs = int(secs)
    milisecs = int((secs - wholesecs)*100)
    hh = wholesecs / 3600
    hhd = hh % 24
    mm = (wholesecs / 60) - (hh*60)
    ss = wholesecs - (hh*3600) - (mm*60)
    return "%.2d:%.2d:%.2d.%.2d" % (hhd,mm,ss,milisecs) 


def f2tc(f,base=25):
    """Converts frames to timecode"""
    try:
        f = int(f)
    except:
        return "--:--:--.--"
    hh = (f / base) / 3600
    mm = ((f / base) / 60) - (hh*60)
    ss = (f/base) - (hh*3600) - (mm*60)
    ff = f - (hh*3600*base) - (mm*60*base) - (ss*base)
    return "%.2d:%.2d:%.2d:%.2d" % (hh,mm,ss,ff) 
 
 
def s2tc(s,base=25):
    """Converts seconds to timecode"""
    try:    f = int(s*base)
    except: return "--:--:--:--"
    hh = (f / base) / 3600
    hhd = (hh%24)
    mm = ((f / base) / 60) - (hh*60)
    ss = (f/base) - (hh*3600) - (mm*60)
    ff = f - (hh*3600*base) - (mm*60*base) - (ss*base)
    return "%.2d:%.2d:%.2d:%.2d" % (hhd,mm,ss,ff) 
 
 
def s2words(s):
    s = int(s)
    if s < 60:     return "%d seconds"%s
    elif s < 120:  return "1 min %d secs" % (s-60)
    elif s < 7200: return "%d minutes" % round(s/60)
    else:          return "%d hours" % round(s/3600)


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
