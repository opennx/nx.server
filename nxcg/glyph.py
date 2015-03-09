#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nxcg.common import *

__all__ = ["glyph"]

class Glyph():
    def __init__(self):
        self.data = {}

    def __call__(self, key, **kwargs):
        return self[key]

    def __getitem__(self, key):
        assert type(key) == str

        if key in self.data:
            g, mtime = self.data[key]
            if not os.path.exists(key) or mtime >= os.path.getmtime(key):
                return g

        if os.path.splitext(key)[1].lower() == ".png":
            g = cairo.ImageSurface.create_from_png(glyph)

        else:
            logging.error("Glyph format \"{}\" is not implemented".format(os.path.splitext(key)[1][1:]))
            return None

        self.data[key] = g, time.time()
        return g

glyph = Glyph()