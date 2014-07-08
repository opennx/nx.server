from .common import DramaticaObject, DramaticaAsset
from .scheduling import DramaticaBlock
from .timeutils import *

class DramaticaTemplate(DramaticaObject):
    def __init__(self, rundown, **kwargs):
        super(DramaticaTemplate, self).__init__(**kwargs)
        self.rundown = rundown
        self.cache = rundown.cache

    @property 
    def dow(self):
        return self.rundown.dow

    def add_block(self, clock, **kwargs):
        if type(clock) == str:
            hh, mm = [int(i) for i in clock.split(":")]
        elif type(clock) in [tuple, list]:
            hh, mm = clock
        block = DramaticaBlock(self.rundown, **kwargs)
        block["start"] = self.rundown.clock(hh, mm)
        self.rundown.add(block)

    def configure(self, **kwargs):
        self.rundown.blocks[-1].config.update(kwargs)

    def apply(self):
        pass