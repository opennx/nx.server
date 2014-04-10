#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import imp
import datetime

from nx import *
from nx.assets import Asset
from nx.items import Event, Bin, Item
from nx.plugins import plugin_path

import dramatica

USE_TAGS = [
    "description",
    "genre/music",
    "genre/movie",
    "rights",
    "mark_in",
    "mark_out",
    "source",
    "identifier/vimeo",
    "identifier/youtube",
    "identifier/main",
    "role/director",
    "role/composer",
    "title",
    "album",
    "duration",
    "qc/state",
    "role/performer",
    "id_folder",
    "path"
]



class DramaticaRunner(dramatica.Dramatica):

    def load_data(self, id_channel, db=False):
        logging.debug("Loading asset cache")
        if not db:
            db = DB()
        db.query("SELECT id_object FROM nx_assets WHERE origin in ('Acquisition', 'Library')")
        for id_asset, in db.fetchall():
            asset = Asset(id_asset)
            for key in USE_TAGS:
                value = asset[key]
                if not value:
                    continue
                value = self.rundown.db.sanit(value)
                value = value.encode("utf-8")
                try:
                    self.rundown.db.query("INSERT INTO assets (id_asset, tag, value) VALUES ({}, '{}', '{}')".format(id_asset, key, value))
                except:
                    print (value)
                    sys.exit(-1)

        logging.debug("Loading history cache")
        db.query("SELECT id_magic, start FROM nx_events WHERE id_channel={}".format(id_channel))
        res = db.fetchall()
        for id_bin, start in res:
            db.query("SELECT id_asset FROM nx_items WHERE id_bin ={}".format(id_bin))
            i = 0
            for id_asset, in db.fetchall():
                self.rundown.db.query("INSERT INTO history (ts, id_asset) VALUES ({}, {})".format(start+i, id_asset))
                i+=1
        self.rundown.db.commit()
        logging.debug("Done")



    def on_structure(self, date, id_channel):
        db = DB()

        start_time = datestr2ts(date)
        end_time   = start_time + (3600*24)

        db.query("SELECT id_object FROM nx_events WHERE id_channel={} AND start > {} and start < {}".format(id_channel, start_time, end_time))
        for id_event, in db.fetchall():
            event = Event(id_event, db=db)
            bin = event.get_bin()
            bin.delete()
            event.delete()

        day = [int(i) for i in date.split("-")]
        self.rundown["day"] = day
        self.rundown["id_channel"] = id_channel
        self.rundown.structure()



        for i, block in enumerate(self.rundown.blocks):
            scheduled_start = time.strftime("%H:%M", time.localtime(block.scheduled_start))
            scheduled_end   = time.strftime("%H:%M", time.localtime(block.scheduled_end))
            print ("\n")
            print (scheduled_start, scheduled_end,  block["title"])

            event = Event()
            bin = Bin()
            bin.save()
            event["id_magic"] = bin.id
            event["id_channel"] = id_channel
            event["start"] = block.scheduled_start
            event["stop"]  = block.scheduled_end

            
            for key in block.meta:
                if key in ["title", "description", "promoted"]:
                    event[key] = block[key]
            event["dramatica/config"] = json.dumps(block.meta)


            for j, item_data in enumerate(block.items):
                j+=1

                item = Item()
                item["id_bin"] = bin.id
                item["position"] = j
                
                if item_data["id_asset"]:
                    item["id_asset"] = int(item_data["id_asset"])
                else:
                    item["title"] = item_data["title"]
                
                item["dramatica/config"] = json.dumps(item_data.meta)

                bin.items.append(item)

            bin.save()
            event.save()



    def on_cleanup(self, date, id_channel):
        db = DB()

        start_time = datestr2ts(date)
        end_time   = start_time + (3600*24)

        db.query("SELECT id_object FROM nx_events WHERE id_channel={} AND start > {} and start < {}".format(id_channel, start_time, end_time))
        for id_event, in db.fetchall():
            event = Event(id_event, db=db)
            bin = event.get_bin()            

            if event["dramatica/config"]:
                dconf = json.loads(event["dramatica/config"])
                self.rundown.add(dconf["block_type"], **dconf)
            else:
                self.rundown.add("UserBlock")

            for item in bin.items:
                
                if item["dramatica/config"]:
                    bitem = dramatica.BlockItem(**json.loads(item["dramatica/config"]))
                else:
                    bitem = dramatica.BlockItem(title=item["title"], id_asset=item["id_asset"], duration=item.get_duration())
                self.rundown.blocks[-1].add(bitem)

            _start = datetime.datetime.fromtimestamp(event["start"])
            self.rundown.blocks[-1]["start_time"] = (_start.hour, _start.minute)
            self.rundown.blocks[-1]["id_bin"] = bin.id



        for block in self.rundown.blocks:
            block.render()
            bin = Bin(block["id_bin"])

            for j, item_data in enumerate(block.items):
                j+=1

                item = Item()
                item["id_bin"] = bin.id
                item["position"] = j
                
                if item_data["id_asset"]:
                    item["id_asset"] = int(item_data["id_asset"])
                else:
                    item["title"] = item_data["title"]
                
                item["dramatica/config"] = json.dumps(item_data.meta)

                bin.items.append(item)




if __name__ == "__main__":
    bpath = os.path.join(plugin_path,"programme")
    
#    drama = DramaticaRunner(bpath)
#    drama.load_data(1)
#    drama.on_structure(time.strftime("%Y-%m-%d"), 1)

    drama = DramaticaRunner(bpath)
    drama.load_data(1)
    drama.on_cleanup(time.strftime("%Y-%m-%d"), 1)

    drama.show()