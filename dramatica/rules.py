class DramaticaRule(object):
    ruleset=[]
    def __init__(self, solver):
        self.solver  = solver
        self.block   = solver.block
        self.cache   = solver.block.cache
        self.assets  = solver.block.cache.assets.values()
 
    def set_weight(self, *args):
        if len(args) == 3:
            id_asset, rule, weight = args
        elif len(args) == 2:
            id_asset, weight = args
            rule = self.ruleset[0]

        self.block.rundown.weights.set_weight(id_asset, rule, weight)

    def clear(self):
        for asset in self.assets:
            self.set_weight(asset.id, 0)

    def rule(self):
        pass

class DramaticaRundownRule(DramaticaRule):
    pass

class DramaticaBlockRule(DramaticaRule):
    pass

class DramaticaItemRule(DramaticaRule):
    pass


##########################################################################################################
## Rundown rules

class PromotedRule(DramaticaRundownRule):
    ruleset = ["promoted"]
    def rule(self):
        for asset in self.assets:
            if asset["promoted"]:
                self.set_weight(asset.id, 1)


class RepetitionRule(DramaticaRundownRule):
    ruleset = ["distance", "repetition"]
    def rule(self):
        f_distances = {} 
        f_runs = {}

        for asset in self.assets:
            runs = self.cache.query("SELECT tstamp FROM history WHERE id_asset = ? ORDER BY ABS(tstamp-?)",
                [asset.id, self.block.scheduled_start],
                one_column=True
                )

            asset["dramatica/runs"] = runs

            if not runs:
                continue

            id_folder = asset["id_folder"]

            if not id_folder in f_runs:
                f_runs[id_folder] = [len(runs)]
            else:
                f_runs[id_folder].append(len(runs))

            val = abs(runs[0] - self.block.scheduled_start)
            if not id_folder in f_distances:
                f_distances[id_folder] = [val]
            else:
                f_distances[id_folder].append(val)

        f_dist_avgs = {}
        f_runs_avgs = {}
        f_dist_maxs = {}
        f_dist_mins = {}

        for id_folder in f_distances.keys():
            f_dist_avgs[id_folder] = self.get_avg(f_distances[id_folder])
            f_runs_avgs[id_folder] = self.get_avg(f_runs[id_folder])
            f_dist_maxs[id_folder] = max(f_distances[id_folder])
            f_dist_mins[id_folder] = min(f_distances[id_folder])

        for asset in self.assets:
            runs = asset["dramatica/runs"]
            id_folder = asset["id_folder"]

            if not runs:
                self.set_weight(asset.id, "distance", 1)
                self.set_weight(asset.id, "repetition", 1)
                continue

            dist = abs(runs[0] - self.block.scheduled_start)
            zd = f_dist_maxs[id_folder] - f_dist_mins[id_folder]
            cd = dist - f_dist_mins[id_folder]
            if zd == 0:
                pd = 1
            else:
                pd = cd/zd
            w  = round(pd, 2)
            self.set_weight(asset.id, "distance", w)

            zr = max(f_runs[id_folder]) - min(f_runs[id_folder])
            cr = len(runs) - min(f_runs[id_folder])
            if zr == 0:
                pr = 1
            else:
                pr = float(cr)/zr
            w+= round(pr, 2)
            self.set_weight(asset.id, "repetition", w)

    def get_avg(self, array):
        """Reimplement this if you don't like results"""
        return array[int(len(array)/2)]


## Rundown rules
##########################################################################################################
## Block rules

class MatureContentRule(DramaticaBlockRule):
    ruleset = ["mature_content"]
    def rule(self):
        for asset in self.assets:
            if asset["contains/nudity"] and self.block["start"] < self.block.rundown.clock(22,0):
                asset["dramatica/veto_reason"] = "Mature content"
                self.set_weight(asset.id, -1)

class GenreRule(DramaticaBlockRule):
    ruleset = ["genre"]
    def rule(self):
        genres = self.block.config.get("genres", [])
        for asset in self.assets:
            if asset["genre"] in genres:
               self.set_weight(asset.id, 1)

class RundownRepeatRule(DramaticaBlockRule):
    ruleset = ["rundown_repeat"]
    def rule(self):
        for asset in self.assets:
            if self.block.rundown.has_asset(asset.id):
                if asset["id_folder"] in [1, 2]: # Do not repeat movies and series in same day
                    asset["dramatica/veto_reason"] = "Rundown repeat"
                    self.set_weight(asset.id, -1)
                    continue
                continue
            self.set_weight(asset.id, 1)

## Block rules
##########################################################################################################
## Item rules

class ArtistSpanRule(DramaticaItemRule):
    ruleset = ["artist_span"]
    def rule(self):
        if asset["id_folder"] == 5:
            pass
            # TODO:
            #  - check if artist is in current block.
            #  - if not use following query

            #asset["dramatica/last_same_artist"] = self.block.cache.query(
            #    "SELECT h.tstamp FROM history as h. assets as a WHERE h.id_asset = a.id_asset AND a.`role/performer` = ? ORDER BY ABS(tstamp - ?) ASC LIMIT 1", 
            #    [asset["role/performer"], self.block.scheduled_start] )




def get_rules():
    from inspect import isclass
    for rule in globals().values():
        if not (isclass(rule) and (issubclass(rule, DramaticaBlockRule) or issubclass(rule, DramaticaRundownRule))):
            continue
        if rule.ruleset:
            yield rule
           