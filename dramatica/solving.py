import math
import random

from .timeutils import *

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
            _newitems = [item for item in block.items if not (item["dramatica/config"] or item["dramatica/solved"])]
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
                self.block.cache.set_weight(id_asset, weight, auto_commit=False)
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

        q = "SELECT id_object FROM assets WHERE {}  ORDER BY {} LIMIT 1".format(conds, order)
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
        if self.asset["genre/music"] in genres or self.asset["genre/movie"] in genres:
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

class BlockRepeatRule(DramaticaItemRule):
    def rule(self):
        if self.asset.id in [a.id for a in self.block.items]:
            return 0
        return 1



class DefaultSolver(DramaticaSolver):
    rules = [
        [GenreRule, 2],
        [PromotedRule, 1],
        [DistanceRule, 1]
        ]

    def solve(self):
        suggested = suggested_duration(self.block.duration)
        print suggested

        if self.block.remaining > (suggested - self.block.duration):

            asset = self.get(
                    "duration < {}".format(self.block.target_duration - suggested),  #FIX MARK IN AND OUT
                    "duration > {}".format(suggested-self.block.duration),
                    "`dramatica/weight` > 0",
                    order="duration DESC"
                ) 

            if asset:
                print asset, "to ", self.block["title"]
                n = self.block.rundown.insert(
                        self.block.block_order+1, 
                        start=self.block["start"] +  suggested,
                        title=asset["title"],
                        description=asset["description"]
                    )
                n.add(asset)


        while self.block.remaining > 0:

            asset = self.get(order="ABS({} - duration )".format(self.block.remaining)) # FIX MARK IN AND OUT
            if self.block.remaining - asset.duration < 0:
                self.block.add(asset)
                break

            asset = self.get("id_folder = 1") ### MOOD/BPM SELECTOR GOES HERE
            self.block.add(asset)

            print (self.block.remaining, asset, asset.duration)






class MusicBlockSolver(DramaticaSolver):
    full_clear = True
    rules = [
        [GenreRule, 2],
        [PromotedRule, 1],
        [DistanceRule, 1]
    ]

    def solve(self):
        jingle_span = 600
        promo_span = 1000
        
        last_jingle = 0
        last_promo  = 0

        jingle_selector = self.block.config.get("jingles", False)

        intro_jingle = self.block.config.get("intro_jingle", False)
        if intro_jingle:
            self.block.add(self.get(intro_jingle, allow_reuse=True))

        while self.block.remaining > 0:
            if self.block.remaining > promo_span and self.block.duration - last_promo > promo_span:
                pass #TODO

            if jingle_selector and self.block.remaining > jingle_span and self.block.duration - last_jingle > jingle_span:
                self.block.add(self.get(jingle_selector, allow_reuse=True))
                last_jingle = self.block.duration

            asset = self.get("id_folder = 1", order="ABS({} - duration )".format(self.block.remaining)) # FIX MARK IN AND OUT
            if self.block.remaining - asset.duration < 0:
                self.block.add(asset)
                break

            asset = self.get("id_folder = 1") ### MOOD/BPM SELECTOR GOES HERE
            self.block.add(asset)

        outro_jingle = self.block.config.get("outro_jingle", False)
        if outro_jingle:
            self.block.add(self.get(outro_jingle, allow_reuse=True))