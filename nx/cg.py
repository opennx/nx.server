#!/usr/bin/env python
# -*- coding: utf-8 -*-

from nx.common.core import logging

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


class CG():
    def __init__(self,width,height):
        self.w = width
        self.h = height
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        self.ctx     = cairo.Context (self.surface)
        self.ctx.set_antialias(cairo.ANTIALIAS_GRAY)


    def rect(self, x, y, w, h, color):
        r, g, b, a = hex_color(color)
        self.ctx.set_source_rgba(r,g,b,a)
        self.ctx.rectangle(x,y,w,h)
        self.ctx.fill()

    def text_box(self, x, y, size, text, fcolor="#efefef", bcolor="#00000066", hoffset=0, fixw=False):
        tsize = int(size*.72)
        self.ctx.set_font_size(tsize)
        tx, ty, tw, th, dx, dy = self.ctx.text_extents(text)
        bw = tw+int(size/2) + hoffset*2
        bh = size
        if fixw: bw = fixw
        self.rect(x, y, bw, bh, bcolor)
        self.ctx.move_to(x+int(bw/2 - tw/2)+hoffset,y+tsize*1.1 )
        r, g, b, a = hex_color(fcolor)
        self.ctx.set_source_rgba(r,g,b,a)
        self.ctx.show_text(text)
        self.ctx.stroke()

    def save(self, fname):
        self.surface.write_to_png(fname)
