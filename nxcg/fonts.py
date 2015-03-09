#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["fonts"]

import pango

class Fonts():
    def __init__(self):
        self.data = {}

    def __getitem__(self, key):
        if not key in self.data:
            font = self.__getfont(key)
            self.data[key] = font
        return self.data[key]

    def __getfont(self, font_description):
        return pango.FontDescription(font_description)

fonts = Fonts()