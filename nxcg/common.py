#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import array


#
# Nebula integration imports
#

try:
    from nx import logging
except ImportError:
    class Logger():
        def debug (self, *args):
            print ("DEBUG  ", " ".join(args))
        def info (self, *args):
            print ("INFO   ", " ".join(args))
        def warning (self, *args):
            print ("WARNING", " ".join(args))
        def error (self, *args):
            print ("ERROR  ", " ".join(args))
    logging = Logger()

try:
    from nx.plugins import plugin_path
    plugin_path = os.path.join(plugin_path, "nxcg")
except ImportError:
    plugin_path = "plugins"


#
# Import graphics libraries
#


import cairo

try:
    import pango
    import pangocairo
except ImportError:
    has_pango = False
    logging.warning("Pango is not installed. Text rendering will suck (or will not work at all)")
else:
    has_pango = True


try:
    from PIL import Image
except ImportError:
    has_pil = False
    logging.warning("PIL is not installed. Image processing will not work")
else:
    has_pil = True


def pil2cairo(im):
    w, h = im.size
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    s = im.tostring('raw', 'BGRA')
    a = array.array('B', s)
    dest = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(dest)
    non_premult_src_wo_alpha = cairo.ImageSurface.create_for_data(a, cairo.FORMAT_RGB24, w, h)
    non_premult_src_alpha = cairo.ImageSurface.create_for_data(a, cairo.FORMAT_ARGB32, w, h)
    ctx.set_source_surface(non_premult_src_wo_alpha)
    ctx.mask_surface(non_premult_src_alpha)
    return dest


def cairo2pil(surface):
    assert type(surface) == cairo.ImageSurface
    w = surface.get_width()
    h = surface.get_height()
    return Image.frombuffer("RGBA", (w, h), surface.get_data(), "raw", "BGRA", 0, 1)