#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import time


MON, TUE, WED, THU, FRI, SAT, SUN = range(0, 7)
JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC = range(0, 12)


def dur(tc):
    """Returns second count from timecode specified as "HH:MM:SS"""
    hh, mm, ss = [int(i) for i in tc.split(":")]
    return hh*3600 + mm*60 + ss

def today():
    t = datetime.date.today()
    return (t.year, t.month, t.day)

def datestr2ts(datestr, hh=0, mm=0, ss=0):
    yy,mo,dd = [int(i) for i in datestr.split("-")]
    ttuple = [yy, mo, dd, hh, mm]
    dt = datetime.datetime(*ttuple)
    tstamp = time.mktime(dt.timetuple()) 
    return tstamp


def suggested_duration(dur):
    adur = int(dur) + 360
    g = adur % 300
    if g > 150:
        r =  adur-g + 300
    else:
        r =  adur -g
    return r