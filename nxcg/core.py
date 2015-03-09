#!/usr/bin/env python
# -*- coding: utf-8 -*-

import imp

from nxcg.common import *
from nxcg.colors import *
from nxcg.glyph import *
from nxcg.fonts import *


__all__ = ["CG"]


class Pango():
    def __init__(self, parent):
        self.parent = parent
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, parent.width, parent.height)
        self.context = cairo.Context(self.surface)
        self.pango_context = pangocairo.CairoContext(cairo.Context(self.surface))
        self.pango_context.set_antialias(cairo.ANTIALIAS_SUBPIXEL)
        self.layout = self.pango_context.create_layout()

    def set_color(self, color):
        self.pango_context.set_source_rgba(*colors(color))

    def set_font(self, font_description):
        font = fonts[font_description]
        self.layout.set_font_description(font)




class CG():
    def __init__(self, width=1920, height=1080):
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        self.context = cairo.Context(self.surface)
        self.width  = width
        self.height = height
        self.pango = False
        self.plugins = []

        if os.path.exists(plugin_path):
            for fname in os.listdir(plugin_path):
                self.load_plugin(fname)

    def load_plugin(self, fname):
        mod_name, file_ext = os.path.splitext(fname)
        if file_ext != ".py":
            return

        py_mod = imp.load_source(mod_name, os.path.join(plugin_path, fname))

        if not "Plugin" in dir(py_mod):
            logging.warning("No plugin class found in {}".format(fname))

        self.plugins.append(py_mod.Plugin(self))
        if hasattr(self.plugins[-1], "on_init"):
            self.plugins[-1].on_init()


    def __getattr__(self, attr):
        for plugin in self.plugins:
            if hasattr(plugin, attr):
                return getattr(plugin, attr)

    @property
    def colors(self):
        return colors

    @property
    def fonts(self):
        return fonts


    def save(self, file_name):
        with open(file_name, "wb") as image_file:
            self.surface.write_to_png(image_file)

    def set_color(self, color):
        self.context.set_source_rgba(*colors(color))

    def rect(self, x, y, w, h):
        self.context.rectangle(x, y, w, h)
        self.context.fill()

    def filter(self, f):
        im = cairo2pil(self.surface)
        im = im.filter(f)
        self.glyph(pil2cairo(im))

    def polygon(self, *args, **kwargs):
        for x, y in args:
            pass #TODO

    def glyph(self, g, x=0, y=0, alignment=7):
        if type(g) == str:
            g = glyph(g)
        if not g or type(g) != cairo.ImageSurface:
            return False
        w, h = g.get_width(), g.get_height()
        if alignment in [4,5,6]:
            y -= int(h/2)
        elif alignment in [1,2,3]:
            y -= h
        if alignment in [8,5,2]:
            x -= int(w/2)
        elif alignment in [9,6,3]:
            x -= w
        self.context.set_source_surface(g, x, y)
        self.context.rectangle(x, y, x + w, y + h)
        self.context.fill()
        return True




    def text(self, text, **kwargs):
        self.pango = Pango(self)

        if "spacing" in kwargs:
            self.pango.layout.set_spacing(kwargs["spacing"] * pango.SCALE)

        if "width" in kwargs:
            self.pango.layout.set_wrap(pango.WRAP_WORD)
            self.pango.layout.set_width(kwargs["width"] * pango.SCALE)

        if "align" in kwargs:
            self.pango.layout.set_alignment(
                    {
                    7 : pango.ALIGN_LEFT,
                    8 : pango.ALIGN_CENTER,
                    9 : pango.ALIGN_RIGHT
                    }[int(kwargs["align"])]
                )

        self.pango.set_font(kwargs.get("font", "Sans 36"))
        self.pango.set_color(kwargs.get("color", FALLBACK_COLOR))

        self.pango.layout.set_markup(text.strip())
        self.pango.pango_context.update_layout(self.pango.layout)

        if kwargs.get("render", True):
            self.text_render(*(kwargs.get("pos", False) or (0,0)))

        w, h = self.pango.layout.get_size()
        if "width" in kwargs and kwargs.get("align", "l") != "l":
            w = kwargs["width"] * pango.SCALE
        return w / pango.SCALE, h / pango.SCALE

    def text_render(self, x, y):
        self.pango.pango_context.show_layout(self.pango.layout)
        self.glyph(self.pango.surface, x, y)

