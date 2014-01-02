#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import *


class Machina:
    def __init__(self):
        self._out = {}
        self._memFile    = "/proc/meminfo"
        self._cpuFile    = "/proc/cpuinfo"
        self._uptimeFile = "/proc/uptime"
        self._loadFile   = "/proc/loadavg"
        self._statFile   = "/proc/stat"

    def _readStat(self):
        cpuStat = {}
        statFile = open( self._statFile , 'r').readlines()
        
        for l in statFile:
           lk = [lk.strip() for lk in l.split()]
         
           if lk[0].lower() == 'cpu': 
              cpuStat['user'] = lk[1];
              cpuStat['nice'] = lk[2];
              cpuStat['system'] = lk[3];
              cpuStat['idle'] = lk[4];
              cpuStat['iowait'] = lk[5];
              cpuStat['irq'] = lk[6];
              cpuStat['softirq'] = lk[7];
              
        self._out['cpuStat'] = cpuStat
        
    def _readUptime(self):
        uptimeFile = open( self._uptimeFile , 'r').read()
        res = uptimeFile.split();
        self._out['uptime'] = {'uptime': res[0], 'idle': res[1]}
        
    def _readLoad(self):
        loadFile = open( self._loadFile , 'r').read()
        res = loadFile.split();
        self._out['loadavg'] = {'1m': res[0], '5m': res[1], '15m': res[2], 'proc': res[3], 'total': res[4] }
      
    def _readMem(self):
        memStat = {}
        memFile = open( self._memFile , 'r').readlines()
        
        for l in memFile:
            lk = [lk.strip() for lk in l.split(':')]
           
            if lk[0].lower() == 'memtotal': 
                memStat[lk[0]] = lk[1]
            elif lk[0].lower() == 'memfree': 
                memStat[lk[0]] = lk[1]
            elif lk[0].lower() == 'buffers': 
                memStat[lk[0]] = lk[1]
            elif lk[0].lower() == 'active': 
                memStat[lk[0]] = lk[1]
            elif lk[0].lower() == 'inactive': 
                memStat[lk[0]] = lk[1]
           
        self._out['memInfo'] = memStat
          
    def _readCpu(self):
        cpuStat = {}
        cpuFile = open( self._cpuFile , 'r').readlines()
      
        cpuStat['cpuThreads'] = 0
      
        for l in cpuFile:
            lk = [lk.strip() for lk in l.split(':')]
         
            if lk[0].lower() == 'processor': 
                cpuStat['cpuThreads']+=1
              
            elif lk[0].lower() == 'model name': 
                w = [w.strip() for w in lk[1].split()]
                cpuStat['model'] = " ".join(w)
            elif lk[0].lower() == 'cpu mhz': 
                cpuStat['clock'] = lk[1]
            elif lk[0].lower() == 'cache size': 
                cpuStat['cache'] = lk[1]
            elif lk[0].lower() == 'cpu cores': 
                cpuStat['physicalCores'] = lk[1]
            elif lk[0].lower() == 'siblings': 
                cpuStat['threadsInfo'] = lk[1]
      self._out['cpuInfo'] = cpuStat
      
    def status(self):
        if PLATFORM == 'windows':
            self._out['status'] =  'Error'
            self._out['message'] = 'Unsupported OS'
        else:
            self._out['status'] = 'Ok'
            self._out['message'] = 'Getting base HW info'
            self._readUptime()
            self._readLoad()
            self._readCpu()
            self._readMem()
            self._readStat()
        return self._out
