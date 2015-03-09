#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from nxcg.common import *

__all__ = ["glyph"]





class Glyph():
    def __init__(self):
        self.data = {}

    def __call__(self, key, **kwargs):
        return self[key]

    def __getitem__(self, key):
        assert type(key) == str, "Glyph key must be string"

        if key in self.data:
            g, mtime = self.data[key]
            if not os.path.exists(key) or mtime >= os.path.getmtime(key):
                return g

        if os.path.splitext(key)[1].lower() == ".png":
            g = cairo.ImageSurface.create_from_png(glyph)
        elif has_pil:
            im = Image.open(key)
            g = pil2cairo(im)
        else:
            return None

        self.data[key] = g, time.time()
        return g

glyph = Glyph()