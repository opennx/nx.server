#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
site_name: network-wide unique indentifier of NX instance.
"""
site_name = "OpenNX"


"""
db_driver: can be "sqlite" or "postgres"
if "sqlite" is used, db_host should be a s3db filename.
"""

db_driver = "sqlite"
db_host   = "demo.s3db"
db_name   = False
db_user   = False
db_pass   = False

"""
cache_driver: can be "internal" or "memcached"
if "memcached" is used, cache_host and cache_port must be specified
"internal" is for testing/debug only! It sucks!
"""

cache_driver = "internal"
cache_host   = False
cache_port   = False
