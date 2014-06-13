class DramaticaRule(object):
    def __init__(self, block, asset):
        self.block = block
        self.asset = asset

    def rule(self):
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
        self.pool = []

        if self.full_clear:
            block.items = []
        else:
            _newitems = [item for item in block.items if not (item["dramatica/config"] or item["dramatica/solved"])]
            block.items = _newitems

        self.create_pool()




    def create_pool(self):        
        for id_asset in self.block.cache.assets:
            i = 0
            for rule_class, weight in self.rules:
                i+=1
                if not issubclass(rule_class, DramaticaBlockRule):
                    continue
                rule = rule_class(self.block, self.block.cache[id_asset])
                weight = rule.rule()
                if weight >= 0:
                    self.block.cache[id_asset].weights[i] = weight
                    self.pool.append(id_asset)

    def get(self, position=False):
        if position:
            pass

        for id_asset in self.block.cache.assets:
            self.block.cache[id_asset].item_weight = 0

    def solve(self):
        pass


## Solver core
########################################################################3
## TESTING MODS






class GenreRule(DramaticaBlockRule):
    def rule(self):
        genres = self.block.config.get("genres",[])
        if self.asset["genre/music"] in genres or self.asset["genre/movie"] in genres:
            return 0
        return -1


class BlockRepeatRule(DramaticaItemRule):
    def rule(self):
        if self.asset.id in [a.id for a in self.block.items]:
            return 0
        return 1






class DefaultSolver(DramaticaSolver):
    rules = [

    ]


class MusicBlockSolver(DramaticaSolver):
    full_clear = True
    rules = [
        [GenreRule, 1]
    ]

    def solve(self):
        print self.block.remaining
