from __future__ import print_function

import math
import sys

from .timeutils import *
from .rules import DramaticaRundownRule, DramaticaBlockRule, DramaticaItemRule, get_rules

def DEBUG(*args):
    print (*args)

SAFE_OVER = 120
ASSET_TO_BLOCK_INHERIT = [
    "title",
    "title/subtitle",
    "description",
    "promoted"
    ]

class DramaticaWeights():
    def __init__(self, rundown):
        self.data = {}
        self.rules = {}
        self.rule_algs = []
        self.rundown = rundown

        i = 0
        for rule in get_rules():
            self.rule_algs.append(rule)
            for rule_name in rule.ruleset:
                self.rules[rule_name] = i
                i+=1

        for asset in self.rundown.cache.assets.values():
            self.data[asset.id] = [0]*i

    def set_weight(self, id_asset, rule, value):
        self.data[id_asset][self.rules[rule]] = value

    def get_weight(self, id_asset, rule):
        try:
            return self.data[id_asset][self.rules[rule]]
        except:
            return 0



class DramaticaSolver(object):
    full_clear = False          # Clear all existing items (including those created by user before solving)

    def __init__(self, block, **kwargs):
        self.block   = block
        self.cache   = block.cache
        self.assets  = block.cache.assets.values()
        self.rundown = block.rundown
        self.kwargs  = kwargs

        if self.full_clear:
            block.items = []
        else:
            _newitems = [item for item in block.items if not str(item["is_optional"]) == "1"]
            block.items = _newitems

        if not hasattr(self.rundown, "weights"):
            self.rundown.weights = DramaticaWeights(self.rundown)
            self.compute_rundown_weights()
        self.compute_block_weights()

    def compute_rundown_weights(self):    
        for rule in self.weights.rule_algs:
            if issubclass(rule, DramaticaRundownRule):
                r = rule(self)
                r.clear()
                r.rule()

    def compute_block_weights(self):
        for rule in self.weights.rule_algs:
            if issubclass(rule, DramaticaBlockRule):
                r = rule(self)
                r.clear()
                r.rule()

    def solve(self):
        pass

    @property 
    def weights(self):
        return self.rundown.weights

    @property
    def used_ids(self):
        return [item.id for item in self.block.items]

    @property
    def veto(self):
        return [i for i in self.weights.data if -1 in self.weights.data[i] ]

    def get_weight(self, *args):
        return self.weights.get_weight(*args)


    def get(self, *args, **kwargs):
        allow_reuse = kwargs.get("allow_reuse", False)
        ordering = kwargs.get("order", [])
        best_fit = kwargs.get("best_fit", False)
        debug    = kwargs.get("debug", False)

        if debug:
            DEBUG("************************************************************************")
            DEBUG("Getting asset", len(self.block.items) ," for block", self.block["title"])

        veto = self.veto
        if not allow_reuse:
            veto = set(veto + self.used_ids)

        if debug:
            DEBUG("VETO:")
            for id_asset in veto:
                asset = self.cache[id_asset]
                DEBUG (" - ", asset, asset["dramatica/veto_reason"] or "Used in block")

        conds = list(args)
        conds.append("id_object NOT IN ({})".format(", ".join([str(i) for i in veto])))
        conds = " AND ".join(conds)

        query = "SELECT id_object FROM assets WHERE {}".format(conds)
        result = self.block.cache.query(query, one_column=True)

        if not result:
            return False

        if debug:
            DEBUG("MATCHING",len(result)," assets:")
            for id_asset in result:
                asset = self.cache[id_asset]
                DEBUG (" - ", asset)

        if not ordering:
            ordering = [
                "weight.genre",
                "weight.distance",
                "weight.repetition",
                "weight.rundown_repeat",
                "weight.promoted"
                ]

        while len(result) > 1:
            for definition in ordering:
                if len(result) == 1:
                    break
                c = int(len(result)/2)
                
                if definition == "weights":
                    result = sorted(result, key=lambda id_asset: sum(self.weights.data[id_asset]), reverse=True)[:c]
                    continue

                definition = definition.split(".")

                if len(definition) < 2:
                    continue
                
                if len(definition) > 2 and definition[2] == "asc":
                    desc = False
                else:
                    desc = True

                if definition[0] == "weight":
                    result = sorted(result, key=lambda id_asset: self.get_weight(id_asset, definition[1]), reverse=desc)
                    if debug:
                        DEBUG("")
                        DEBUG("refined result using", definition)
                        for id_asset in result[:c]:
                            DEBUG (" --- ", 
                                "{:<90}".format(self.cache[id_asset]),  
                                "{:<10}".format(self.get_weight(id_asset, definition[1])), 
                                "({} runs)".format(len(self.cache[id_asset]["dramatica/runs"])),
                                "{:.02f} hours ago".format(abs(self.block.scheduled_start - self.cache[id_asset]["dramatica/runs"][0])/3600) if self.cache[id_asset]["dramatica/runs"] else "",
                                )
                        DEBUG("discarted result", definition)
                        for id_asset in result[c:]:
                            DEBUG (" --- --- ", 
                                "\033[31m",
                                "{:<85}".format(self.cache[id_asset]),  
                                "{:<10}".format(self.get_weight(id_asset, definition[1])), 
                                "({} runs)".format(len(self.cache[id_asset]["dramatica/runs"])),
                                "{:.02f} hours ago".format(abs(self.block.scheduled_start - self.cache[id_asset]["dramatica/runs"][0])/3600) if self.cache[id_asset]["dramatica/runs"] else "",
                                "\033[0m"
                                )

                    result = result[:c]
                        
                elif definition[0] == "meta":
                    result = sorted(result, key=lambda id_asset: self.cache[id_asset][definition[1]], reverse=desc)[:c]
                    if debug:
                        DEBUG(
                            "\nrefined result using", definition)
                        for id_asset in result:
                            DEBUG (" --- ", self.cache[id_asset],  self.cache[id_asset][definition[1]])

                if best_fit:
                    result = sorted(result, key=lambda id_asset: abs(best_fit - self.cache[id_asset].duration))[:1]


        id_asset = result[0]
        asset =  self.block.cache[id_asset]

        if debug:
            DEBUG("\n\033[32mRETURNING\033[0m", asset, "\n\n")

        return asset




















######################################################################################


class DefaultSolver(DramaticaSolver):
    default_block_source = "id_folder = 1"

    def solve_empty(self):
        for id_asset in sorted(self.block.cache.assets, key=lambda x: self.block.cache.assets[x]["dramatica/weight"]):
            if not self.block.cache[id_asset]:
                continue
    
        asset = self.get(
            self.block.config.get("block_source", self.default_block_source),
            "io_duration < {}".format(self.block.remaining + SAFE_OVER),
            order=[
                "weight.genre",
                "weight.distance", 
                "weight.repetition", 
                "meta.io_duration",
                "weight.promoted",
                ]
            )
        if asset:
            self.block.add(asset, is_optional=0, id_asset=asset.id)
            for key in ASSET_TO_BLOCK_INHERIT:
                if asset[key]:
                    self.block[key] = asset[key]


    def insert_block(self, asset, start):
        n = self.block.rundown.insert(
                self.block.block_order+1, 
                start=start,
                id_asset = asset.id,
                is_optional = 0,
            )
        n.config["solve_empty"] = True
        n.add(asset)
        for key in ASSET_TO_BLOCK_INHERIT:
            if asset[key]:
                n[key] = asset[key]

        for v in ["jingles", "promos", "post_main", "block_source", "genres"]:
            if self.block.config.get(v, False):
                n.config[v] = self.block.config[v]


    def insert_post_main(self):
        """
        Inserts clips which should run right after "main" asset.
        Promos, comming up next graphics etc...
        """
        post_main = self.block.config.get("post_main", False)
        if not post_main:
            return
        elif type(post_main) == str:
            post_main = [post_main]

        for definition in post_main:
            asset = self.get(definition)
            if asset:
                self.block.add(asset)        


    def solve(self):
        yield "Solving {}".format(self.block)
        if not self.block.items:
            if self.block.config.get("solve_empty", False):
                self.solve_empty()
            else:
                return


        suggested = suggested_duration(self.block.duration)
        jingles = self.block.config.get("jingles", False)
        fill_source = self.block.config.get("fill_source", "id_folder IN (3,5,7)")
    

        # todo: insert post_main after main.
        self.insert_post_main()

        ##########################################
        ## If remaining time is long, split block

        if self.block.remaining > (suggested - self.block.duration):
            asset = self.get(
                    self.block.config.get("block_source", self.default_block_source),
                    "io_duration < {}".format(self.block.target_duration - suggested),
                    order=[
                        "weight.distance", 
                        "weight.repetition", 
                        "meta.io_duration",
                        "weight.genre",
                        "weight.promoted",
                        ],
                   # debug=True
                ) 

            if asset:
                print ("Splitting block using", asset)
                self.insert_block(asset, start=self.block["start"]+suggested)
            
        ## If remaining time is long, split block
        ##########################################

        while self.block.remaining > 0:
            asset = self.get(fill_source, order=["weight.genre", "weight.rundown_repeat"], best_fit=self.block.remaining)
            if asset and self.block.remaining - asset.duration < 0:
                self.block.add(asset)
                break

            asset = self.get(
                fill_source, 
                "io_duration < {}".format(self.block.remaining + SAFE_OVER),
                order=["weight.genre", "weight.rundown_repeat"]
                ) ### Fillers
            
            if not asset:
                break

            self.block.add(asset)

            if jingles:
                jingle = self.get(jingles, allow_reuse=True)
                if jingle:
                    self.block.add(jingle)





class MusicBlockSolver(DramaticaSolver):
    full_clear = True
    rules = []

    def solve(self):
        yield "Solving {}".format(self.block)
        last_jingle = 0
        last_promo  = 0

        jingle_selector = self.block.config.get("jingles", False)
        promo_selector  = self.block.config.get("promos", False)
        intro_jingle    = self.block.config.get("intro_jingle", False)
        outro_jingle    = self.block.config.get("outro_jingle", False)
        jingle_span     = self.block.config.get("jingle_span",600)
        promo_span      = self.block.config.get("promo_span",1000)
        song_source     = self.block.config.get("song_source", "id_folder = 5")

        if intro_jingle:
            self.block.add(self.get(intro_jingle, allow_reuse=True))

        bpm_median = self.rundown.cache.query("SELECT `audio/bpm` FROM assets WHERE `audio/bpm` NOT NULL ORDER BY `audio/bpm` LIMIT 1 OFFSET (SELECT COUNT(*) FROM assets WHERE `audio/bpm` NOT NULL) / 2")[0][0]
        bpm_mod = True

        while self.block.remaining > 0:
            # PROMOS #
            ##########
            if promo_selector and self.block.remaining > promo_span and self.block.duration - last_promo > promo_span:
                promo = self.get(promo_selector, allow_reuse=False)
                if promo:
                    self.block.add(promo)
                last_promo = self.block.duration

            # JINGLES #
            ###########
            if jingle_selector and self.block.remaining > jingle_span and self.block.duration - last_jingle > jingle_span:
                jingle = self.get(jingle_selector, allow_reuse=True)
                if jingle:
                    self.block.add(jingle)
                last_jingle = self.block.duration

            # FINAL SONG #
            ##############
            asset = self.get(song_source, best_fit=self.block.remaining)
            if self.block.remaining - asset.duration < 0:
                self.block.add(asset)
                break

            # DEFAULT SONG #
            ################
            bpm_mod = not bpm_mod
            if bpm_mod:
                bpm_cond = "`audio/bpm` < {}".format(bpm_median)
            else:
                bpm_cond = "`audio/bpm` > {}".format(bpm_median)
            asset = self.get(song_source, bpm_cond)
            self.block.add(asset)

        if outro_jingle:
            self.block.add(self.get(outro_jingle, allow_reuse=True))


solvers = {
    "MusicBlock" : MusicBlockSolver,
    "Default" : DefaultSolver
    }