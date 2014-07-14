import math
import random

from .timeutils import *

SAFE_OVER = 120
ASSET_TO_BLOCK_INHERIT = [
    "title",
    "description",
    "promoted"
    ]



class DramaticaRule(object):
    def __init__(self, solver, asset=False):
        self.solver = solver
        self.block = solver.block
        self.asset = asset

    def rule(self):
        pass

    def post(self):
        pass

class DramaticaBlockRule(DramaticaRule):
    pass

class DramaticaItemRule(DramaticaRule):
    pass


class DramaticaSolver(object):
    full_clear = False          # Clear all existing items (including those created by user before solving)
    rules = []                  # List of solver rules and their weights -  tuple(rule_class, weight)

    def __init__(self, block, **kwargs):
        self.block = block
        self.args = kwargs

        if self.full_clear:
            block.items = []
        else:
            _newitems = [item for item in block.items if not (str(item["is_optional"]) == 1 or item["dramatica/config"])]
            block.items = _newitems

        self.create_pool()


    @property
    def used_ids(self):
        return [item["id_object"] for item in self.block.items]

    def create_pool(self):        
        self.block.cache.clear_pool_weights()
        self.pool_ids = []

        for id_asset in self.block.cache.assets:
            i = 0
            tweight = 0
            for rule_class, weight in self.rules:
                i+=1
                if not issubclass(rule_class, DramaticaBlockRule):
                    continue
                rule = rule_class(self, self.block.cache[id_asset])
                lweight = rule.rule()
                if lweight == -1:
                    tweight = -1
                    break
                tweight += lweight*weight

            if tweight != 0:
                self.block.cache.set_weight(id_asset, tweight, auto_commit=False)
            if tweight >= 0:
                self.pool_ids.append(id_asset)
        self.block.cache.conn.commit()


        for rule_class, weight in self.rules:
            if not issubclass(rule_class, DramaticaBlockRule):
                continue
            rule = rule_class(self)
            rule.post()



    def get(self, *args, **kwargs):
        allow_reuse = kwargs.get("allow_reuse", False)
        order = kwargs.get("order", "`dramatica/weight` DESC")
        conds = list(args)
        if not allow_reuse:
            cond = "id_object NOT IN ({})".format(", ".join([str(i) for i in self.used_ids]))
            conds.append(cond)

        conds = ["`dramatica/weight` >= 0", "duration > 0"] + conds
        conds = " AND ".join(conds)

        q = "SELECT id_object FROM assets WHERE {} ORDER BY {}, RANDOM() LIMIT 1".format(conds, order)
        self.block.cache.cur.execute(q)
        try:
            id_asset = self.block.cache.cur.fetchall()[0][0]
        except:
            return False

        return self.block.cache[id_asset]

    def solve(self):
        pass


## Solver core
########################################################################3
## TESTING MODS


class GenreRule(DramaticaBlockRule):
    def rule(self):
        genres = self.block.config.get("genres",[])
        if self.asset["genre"] in genres:
            return 1
        return 0

class PromotedRule(DramaticaBlockRule):
    def rule(self):
        return int( self.asset["promoted"] )

class DistanceRule(DramaticaBlockRule):
    def rule(self):
        dist = self.block.cache.run_distance(self.asset.id, self.block.scheduled_start)
        self.asset["dramatica/run_distance"] = dist
        return 0

    def post(self):
        dist_median = sorted(self.solver.pool_ids, key=lambda id_asset: self.block.cache[id_asset]["dramatica/run_distance"])[int(math.floor(len(self.solver.pool_ids)/2))]
        for id_asset in self.solver.pool_ids:
            rdist = self.block.cache[id_asset]["dramatica/run_distance"]
            if rdist == -1:
                w = 2
            elif rdist > dist_median:
                w = 1
            else:
                w = 0  
            self.block.cache.update_weight(id_asset, w, auto_commit=False)
        self.block.cache.conn.commit()


class MatureContentRule(DramaticaBlockRule):
    def rule(self):
        if self.asset["contains/nudity"] and self.block["start"] < self.block.rundown.clock(22,0):
            return -1
        return 0


class RundownRepeatRule(DramaticaBlockRule):
    def rule(self):
        if self.block.rundown.has_asset(self.asset.id):
            if self.asset["id_folder"] in [1, 2]: # Do not repeat movies and series in same day
                return -1
            return 0
        return 1









class DefaultSolver(DramaticaSolver):
    rules = [
        [MatureContentRule, 1],
        [GenreRule, 2],
        [PromotedRule, 1],
        [DistanceRule, 2],
        [RundownRepeatRule, 1]
        ]

    block_source = "id_folder IN (1, 2)"
    fill_source =  "id_folder IN (3,5,7,8)"
    
    def solve(self):
        if not self.block.items:
            asset = self.get(self.block_source)
            self.block.add(asset, is_optional=0, id_asset=asset.id)
            for key in ASSET_TO_BLOCK_INHERIT:
                if asset[key]:
                    self.block[key] = asset[key]

        suggested = suggested_duration(self.block.duration)

        if self.block.remaining > (suggested - self.block.duration):
            asset = self.get(
                    self.block_source,
                    "io_duration < {}".format(self.block.target_duration - suggested),
                    "io_duration > {}".format(suggested-self.block.duration),
                    "`dramatica/weight` > 0",
                    order="`dramatica/weight` DESC, io_duration DESC".format(block_source=self.block_source)
                ) 

            if asset:
                n = self.block.rundown.insert(
                        self.block.block_order+1, 
                        start=self.block["start"] +  suggested,
                        id_asset = asset.id,
                        is_optional = 0
                    )
                n.add(asset)
                for key in ASSET_TO_BLOCK_INHERIT:
                    if asset[key]:
                        n[key] = asset[key]


        while self.block.remaining > 0:
            asset = self.get(self.fill_source, order="ABS({} - io_duration )".format(self.block.remaining))
            if self.block.remaining - asset.duration < 0:
                self.block.add(asset)
                break

            asset = self.get(
                self.fill_source, 
                "io_duration < {}".format(self.block.remaining + SAFE_OVER),
                order = "`dramatica/weight` DESC, RANDOM()"
                ) ### Fillers

            
            self.block.add(asset)






class MusicBlockSolver(DramaticaSolver):
    full_clear = True
    rules = [
        [MatureContentRule, 1],
        [GenreRule, 3],
        [PromotedRule, 1],
        [DistanceRule, 1]
    ]

    song_source = "id_folder = 5"
   
    def solve(self):
        jingle_span = 600
        promo_span = 1000
        
        last_jingle = 0
        last_promo  = 0

        jingle_selector = self.block.config.get("jingles", False)

        intro_jingle = self.block.config.get("intro_jingle", False)
        if intro_jingle:
            self.block.add(self.get(intro_jingle, allow_reuse=True))

        bpm_mod = True
        while self.block.remaining > 0:
            if self.block.remaining > promo_span and self.block.duration - last_promo > promo_span:
                pass #TODO

            if jingle_selector and self.block.remaining > jingle_span and self.block.duration - last_jingle > jingle_span:
                self.block.add(self.get(jingle_selector, allow_reuse=True))
                last_jingle = self.block.duration

            asset = self.get(
                self.song_source, 
                order="`dramatica/weight` DESC, ABS({} - io_duration )".format(self.block.remaining)
                )
            if self.block.remaining - asset.duration < 0:
                self.block.add(asset)
                break

            bpm_mod = not bpm_mod
            if bpm_mod:
                bpm_cond = "`audio/bpm` < (SELECT id_object FROM assets ORDER BY `audio/bpm` LIMIT 1 OFFSET (SELECT COUNT(*) FROM assets) / 2)"
            else:
                bpm_cond = "`audio/bpm` > (SELECT id_object FROM assets ORDER BY `audio/bpm` LIMIT 1 OFFSET (SELECT COUNT(*) FROM assets) / 2)"

            asset = self.get(self.song_source, ordrer="`dramatica/weight` DESC, {} DESC, RANDOM()".format(bpm_cond) ) ### MOOD/BPM SELECTOR GOES HERE
            self.block.add(asset)

        outro_jingle = self.block.config.get("outro_jingle", False)
        if outro_jingle:
            self.block.add(self.get(outro_jingle, allow_reuse=True))
