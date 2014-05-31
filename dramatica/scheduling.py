#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

from .common import DramaticaObject
from .timeutils import *

DEFAULT_BLOCK_DURATION = 600



class DramaticaBlock(DramaticaObject):
    default = {}
    def __init__(self, rundown, **kwargs):
        super(Block, self).__init__(**kwargs)
        self.rundown   = rundown
        self.db          = self.rundown.db
        self.asset       = self.rundown.asset
        self.block_order = len(self.rundown.blocks)
        self.items = []
        self.rendered = False

    @property
    def block_type(self):
        return self.__class__.__name__

    @property
    def duration(self):
        dur = 0
        if self.items:
            for item in self.items:
                dur += item.duration
        else:
            start_time = self.broadcast_start
            end_time   = self.scheduled_end
            dur = self["target_duration"] or end_time - start_time
        return dur

    @property
    def scheduled_start(self):
        if self["start"]:
            return self.rundown.clock(*self["start"])
        elif self.block_order == 0:
            return self.rundown.day_start
        return self.rundown.blocks[self.block_order-1].scheduled_end
        

    @property
    def scheduled_end(self):
        try:
            remaining_blocks = self.rundown.blocks[self.block_order+1:]
        except:
            return self.rundown.day_end

        inter_blocks = 1
        for block in remaining_blocks:
            next_fixed_start = block["start"]
            if next_fixed_start:
                next_fixed_start = self.rundown.clock(*next_fixed_start)
                break
            inter_blocks += 1
        else:
            next_fixed_start = self.rundown.day_end

        scheduled_end = self.scheduled_start + ((next_fixed_start - self.scheduled_start) / inter_blocks)
        if inter_blocks > 1:
            scheduled_end = scheduled_end - (scheduled_end % 300) #Round down to 5 mins
        return scheduled_end



    @property
    def broadcast_start(self):
        if self.block_order == 0:
            return self.rundown.day_start
        return self.rundown.blocks[self.block_order-1].broadcast_end
        

    @property 
    def broadcast_end(self):
        if self.rendered and self.items:
            return self.broadcast_start + self.duration
        else:
            return self.scheduled_end


    def render(self):
        _newitems = [item for item in self.items if item["item_type"] != "placeholder"]
        self.items = _newitems
        self.structure()
        self.rendered = True

    def structure(self):
        """This is going to be reimplemented with actual block structure. Default is placeholder matching block duration"""
        self.add_default_placeholder()
            
    def add(self, item, **kwargs):
        assert type(item) == DramaticaAsset
        self.items.append(item)
        self.items[-1].meta.update(kwargs)









class DramaticaRundown(DramaticaObject):
    default = {
        "day"        : today(),
        "id_channel" : 1,
        "day_start"  : (6,00)
    }

    def __init__(self, **kwargs):
        super(Rundown, self).__init__(**kwargs)
        self.block_types = {}
        self.blocks = []


    def clock(self, hh, mm):
        """Converts hour and minute of current day to unix timestamp"""
        ttuple = list(self["day"]) + [hh, mm]
        dt = datetime.datetime(*ttuple)
        tstamp = time.mktime(dt.timetuple())  
        if tstamp < self.day_start:
            tstamp += 3600*24
        return tstamp

    @property
    def dow(self):
        return datetime.datetime(*self["day"]).weekday()

    @property
    def day_start(self):
        ttuple = list(self["day"]) + list(self["day_start"])
        dt = datetime.datetime(*ttuple)
        return time.mktime(dt.timetuple())  

    @property 
    def day_end(self):
        return self.day_start + (24*3600)

    def add(self, block):
        assert type(block) == DramaticaBlock
        self.blocks.append(block)

    def render(self, force=False):
        self.at_time = self.day_start
        for block in self.blocks:
            if not block.rendered or force:
                block.render()
            self.at_time += block.duration