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

        f_dist_maxs = {}
        f_dist_mins = {}
        f_runs_maxs = {}

        for id_folder in f_distances.keys():
            f_dist_maxs[id_folder] = max(f_distances[id_folder])
            f_dist_mins[id_folder] = min(f_distances[id_folder])
            f_runs_maxs[id_folder] = max(f_runs[id_folder])

        for asset in self.assets:
            runs = asset["dramatica/runs"]
            id_folder = asset["id_folder"]

            if not runs:
                self.set_weight(asset.id, "distance", 1)
                self.set_weight(asset.id, "repetition", 1)
                continue

            # DISTANCE WEIGHT
            dist = abs(runs[0] - self.block.scheduled_start)
            zd = f_dist_maxs[id_folder] - f_dist_mins[id_folder]
            cd = dist - f_dist_mins[id_folder]
            if zd == 0:
                pd = 1
            else:
                pd = cd/zd
            w  = round(pd, 2)
            self.set_weight(asset.id, "distance", w)

            # RUNS WEIGHT
            max_run = f_runs_maxs[asset["id_folder"]]
            w = 1 -  (float(len(asset["dramatica/runs"])) / max_run)
            self.set_weight(asset.id, "repetition", round(w,2))


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
        genres = self.block.config.get("genre", [])
        if type(genres) == str:
            genres = [genres]
        elif not genres:
            genres = []
        for asset in self.assets:
            if asset["genre"] and asset["genre"] in genres:
               self.set_weight(asset.id, 1)

class RundownRepeatRule(DramaticaBlockRule):
    ruleset = ["rundown_repeat"]
    def rule(self):
        data = {}
        for asset in self.assets:
            count =  len(self.block.rundown.has_asset(asset.id)) 
            if count > 0 and asset["id_folder"] in [1, 2]: # Do not repeat movies and series in same day
                asset["dramatica/veto_reason"] = "Rundown repeat"
                self.set_weight(asset.id, -1)
                continue
            data[asset.id] = count
        if not data:
            return
        max_runs = float(max(data.values()))
        if not max_runs:
            return
        for id_asset in data.keys():
            self.set_weight(asset.id, data[id_asset] / max_runs)

## Block rules
##########################################################################################################
## Item rules

class ArtistSpanRule(DramaticaItemRule):
    ruleset = ["artist_span"]
    def rule(self):
        for asset in self.assets:
            if asset["id_folder"] == 5:
                for item in self.block.items:
                     if item["role/performer"] == asset["role/performer"]:
                        self.set_weight(asset.id, 0)
                        break
                else:
                    self.set_weight(asset.id, 1)
            # TODO:
            #  - check if artist is in current block.
            #  - if not use following query

            #asset["dramatica/last_same_artist"] = self.block.cache.query(
            #    "SELECT h.tstamp FROM history as h. assets as a WHERE h.id_asset = a.id_asset AND a.`role/performer` = ? ORDER BY ABS(tstamp - ?) ASC LIMIT 1", 
            #    [asset["role/performer"], self.block.scheduled_start] )

class BlockRepeatRule(DramaticaItemRule):
    ruleset = ["block_repeat"]
    def rule(self):
        data = {}
        for item in self.block.items:
            data[item.id] = data.get(item.id, 0) + 1
        if not data:
            return
        max_runs = float(max(data.values()))
        for asset in self.assets:
            if not max_runs:
                self.set_weight(asset.id, 1)
            elif asset.id in data:
                self.set_weight(asset.id, 1-(data[asset.id] / max_runs))
            else:
                self.set_weight(asset.id, 1)




def get_rules():
    from inspect import isclass
    for rule in globals().values():
        if not (isclass(rule) and (issubclass(rule, DramaticaBlockRule) or issubclass(rule, DramaticaItemRule) or issubclass(rule, DramaticaRundownRule))):
            continue
        if rule.ruleset:
            yield rule
