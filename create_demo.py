#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os



from nx.common import db


db.query("""
CREATE TABLE nx_assets (id_asset INTEGER PRIMARY KEY ASC)

""")




