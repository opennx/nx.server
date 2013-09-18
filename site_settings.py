#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
site_name: network-wide unique indentifier of NX instance.
"""
site_name = "OpenNX"


"""
db_driver: can be "sqlite" or "postgres"
"""

db_driver = "sqlite"
db_host   = "demo.s3db"
db_name   = False
db_user   = False
db_pass   = False

"""
cache_driver: can be "internal" or "memcached"
if "memcached" is used, cache_host and cache_port must be specified
"""

cache_driver = "internal"
cache_host   = False
cache_port   = False
