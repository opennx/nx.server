import sqlite3


def io_dur(dur, mki, mko):
    if not dur: return 0
    if mko > 0: dur -= dur - mko
    if mki > 0: dur -= mki
    return dur


class DramaticaObject(object):
    default = {
        "title" : "Unnamed object"
        }

    def __init__(self, **kwargs):
        self.meta = {}
        self.meta.update(self.default)
        self.meta.update(kwargs)

    def __getitem__(self, key):
        return self.meta.get(key, False)

    def __setitem__(self, key, value):
        self.meta[key] = value


class DramaticaAsset(DramaticaObject):
    default = {
        "is_optional" : 1
    }

    def __init__(self, **kwargs):
        super(DramaticaAsset, self).__init__(**kwargs)
        self.veto = False
        self.weights = {}

    @property 
    def id(self):
        return self["id_object"]

    @property
    def duration(self):
        dur = float(self.meta.get("duration",0))
        mki = float(self.meta.get("mark_in" ,0))
        mko = float(self.meta.get("mark_out",0))
        if not dur: return 0
        if mko > 0: dur -= dur - mko
        if mki > 0: dur -= mki
        return dur

    def __repr__(self):
        t = "Asset ID:{}".format(self.id)
        if self["title"]:
            try:
                t += " ({})".format(self["title"])
            except:
                pass
        return t

class DramaticaCache(object):
    def __init__(self, tags):
        self.conn = sqlite3.connect(":memory:")
        self.cur = self.conn.cursor()
        self.assets = {}
        self.tags = tags + [
            (int, "dramatica/weight"),
            (float, "io_duration")
            ]
        tformat = ", ".join(["`{}` {}".format(tag, {int:"INTEGER", str:"TEXT", float:"REAL"}[t]) for t, tag in self.tags])
        self.cur.execute("CREATE TABLE assets (id_object INTEGER PRIMARY KEY, {})".format(tformat))
        self.cur.execute("CREATE TABLE history (id_channel INTEGER, tstamp INTEGER, id_asset INTEGER)")
        self.conn.commit()

    def load_assets(self, data_source):
        self.cur.execute("DELETE FROM assets;")
        for asset in data_source:
            id_object = asset["id_object"]
            asset["io_duration"] = io_dur(asset.get("duration",0), asset.get("mark_in", 0), asset.get("mark_out", 0))
            self.cur.execute("INSERT INTO assets VALUES (?, {})".format(",".join(["?"]*len(self.tags))), [id_object] + [asset.get(k, None) for t, k in self.tags ])
            self.assets[id_object] = DramaticaAsset(**asset)
        self.conn.commit()
        return len(self.assets)

    def load_history(self, data_source, start=False, stop=False):
        if not (start or stop):
            self.cur.execute("DELETE FROM history;")
        else:
            conds = []
            if start:
                conds.append("tstamp > {}".format(start))
            if stop:
                conds.append("tstamp < {}".format(stop))
            self.cur.execute("DELETE FROM history WHERE {}".format(" AND ".join(conds)))
        self.conn.commit()
        i = 0
        for id_channel, tstamp, id_asset in data_source:
            self.cur.execute("INSERT INTO history VALUES (?,?,?)", [id_channel, tstamp, id_asset])
            i+=1
        self.conn.commit()
        return i
        
    def __getitem__(self, key):
        key = int(key)
        if key in self.assets:
            return self.assets[key]

    def sanit(self, instr):
        try:
            return str(instr).replace("''","'").replace("'","''").decode("utf-8")
        except:
            return instr.replace("''","'").replace("'","''")

    def query(self, *args, **kwargs):
        self.cur.execute(*args)
        if kwargs.get("one_column", False):
            return [i[0] for i in self.cur.fetchall()]
        else:
            return self.cur.fetchall()