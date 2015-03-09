#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os

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
    import PIL
except ImportError:
    has_pil = False
    logging.warning("PIL is not installed. Image processing will not work")
else:
    has_pil = True