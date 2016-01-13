#
# WARNING. THIS LIBRARY IS DEPRECATED!
#

import random

from nx import *
from nx.plugins import plugin_path


try:
    import cairo
except ImportError:
    logging.error("Cairo is not installed")

def hex_color(hex_string):
    h = hex_string.lstrip("#")
    r = int (h[0:2],16) / 255.0
    g = int (h[2:4],16) / 255.0
    b = int (h[4:6],16) / 255.0
    try:    a = int (h[6:8],16) / 255.0
    except: a = 1.0
    return r,g,b,a


def plugins():
    bpath = os.path.join(plugin_path, "cg")

    if not os.path.exists(bpath):
        logging.warning("CG plugins directory does not exist")

    else:
        for fname in os.listdir(bpath):
            mod_name, file_ext = os.path.splitext(fname)
            if file_ext != ".py":
                continue
            plugin = open(os.path.join(bpath, fname)).read()
            yield plugin


class CG(object):
    def __init__(self, width=1920, height=1080):
        self.new(width, height)

    def new(self, width, height):
        self.w = width
        self.h = height
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self.ctx     = cairo.Context (self.surface)
        self.ctx.set_antialias(cairo.ANTIALIAS_GRAY)

    def rect(self, x, y, w, h, color=False):
        if color:
            r, g, b, a = hex_color(color)
            self.ctx.set_source_rgba(r,g,b,a)
        self.ctx.rectangle(x,y,w,h)
        self.ctx.fill()

    def glyph(self, glyph, x=0, y=0, alignment=7):
        if type(glyph) == str and glyph.lower().endswith(".png"):
            if not os.path.exists(glyph):
                print ("Glyph not found")
                return False
            glyph = cairo.ImageSurface.create_from_png(glyph)
        elif type(glyph) == cairo.ImageSurface:
            pass
        else:
            print ("CG: Wrong glyph type")
            return False

        w, h = glyph.get_width(), glyph.get_height()
        if alignment in [4,5,6]:
            y -= int(h/2)
        elif alignment in [1,2,3]:
            y -= h
        if alignment in [8,5,2]:
            x -= int(w/2)
        elif alignment in [9,6,3]:
            x -= w

        self.ctx.set_source_surface(glyph, x, y)
        self.ctx.rectangle(x, y, x + w, y + h)
        self.ctx.fill()
        return True

    def save(self, fname):
        self.surface.write_to_png(fname)

    for plugin in plugins():
        exec(plugin)

