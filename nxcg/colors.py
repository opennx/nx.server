#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["COLOR_PRESETS", "FALLBACK_COLOR", "colors"]

FALLBACK_COLOR = (.7, .7, .7, 1)

COLOR_PRESETS = {
    "iron"            : "#807C8B",
    "graphite"        : "#454343",
    "steel"           : "#536B77",
    "gold"            : "#FBB829",
    "cyan"            : "#00B4FF",
    "orange"          : "#FF6600",
    "red"             : "#CC0000",
    "green"           : "#A1C820",
    "blue"            : "#025D8C",
    "yellow"          : "#EDDE45",

    # TV broadcast related color presets

    "white" : "#EBEBEB",
    "black" : "#101010",

    "black glass 70"  : "#000000B3",
    "black glass 75"  : "#000000CC",
    "black glass 80"  : "#000000E6",

    "logo gray"       : "#F5F5F5B3",

    # Pantone colors of past years

    "emerald"         : "#009B77",
    "tangerine"       : "#DD4124",
    "honeysuckle"     : "#D65076",
    "turquoise"       : "#45B8AC",
    "mimosa"          : "#EFC050",
    "blue izis"       : "#5B5EA6",
    "pepper"          : "#9B2335",
    "sand"            : "#DFCFBE",
    }


def hex_color(hex_string):
    h = hex_string.lstrip("#")
    try:
        r = int(h[0:2], 16) / 255.0
        g = int(h[2:4], 16) / 255.0
        b = int(h[4:6], 16) / 255.0
    except:
        return FALLBACK_COLOR
    try:
        a = int(h[6:8], 16) / 255.0
    except:
        a = 1.0
    return r, g, b, a


class Colors():
    default_color = FALLBACK_COLOR

    def __init__(self):
        self.data = {}
        for k in COLOR_PRESETS:
            self[k] = COLOR_PRESETS[k]

    def __call__(self, key):
        return self[key]

    def __setitem__(self, key, value):
        if type(value) == str and value.startswith("#"):
            self.data[key] = hex_color(value)

    def __getitem__(self, key):
        if type(key) == str:
            key = key.lower()

        if not key in self.data:
            if type(key) == str and key.startswith("#"):
                self.data[key] = hex_color(key)
            else:
                return self.default_color

        return self.data[key]

    def update(self, data):
        for key in data:
            self[key] = data[key]

colors = Colors()