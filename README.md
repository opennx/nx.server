nx.server
=========

## About

OpenNX media asset management core.

_Early pre-alpha version - Only to be used in presence of developers._


## Installation

### Prerequisities
Full installation on Debian Wheezy
* Install postgresql `apt-get install postgresql postgresql-client postgresql contrib`
* Install memcached service `apt-get install memcached`
* Install python modules `apt-get install python-psycopg2 python-pylibmc python-cairo python-beautifulsoup`
* Install ffmpeg `wget https://raw.github.com/opennx/broadcast-tools/master/inst.all && chmod +x inst.all && ./inst.all`
* 

### Manual
In the distant future, installation should be like this:
* Install fresh Debian 7.x machine.
* Log in as root
* Run `wget http://please.nxme.eu -o inst.all && chmod +x inst.all && ./inst.all`
* Grab a beer


## Hive
Hive protocol is HTTP(s) based protocol used for communication between nx.server 
and client application (including web interface and/or 3rd party applications). 
Hive can also serve as playout control proxy (optional).

### Generic responses

* `400` - Bad request, query is malformed
* `401` - Unauthorised. Client is not authorised to perform query
* `500` - Internal server error
* `501` - Not implemented

### Methods

#### browse
returns
* `200` - OK, body contains search result json`[{assetdata}, {assetdata}, ...]`
* `204` - OK, no result, no body sent
* `206` - OK, partial information. There are more matching assets than can be displayed.

#### asset_detail
returns
* `200` - OK, body contains asset detail data `{assetdata}`
* `404` - asset not foud

#### new_asset
returns
* `201` - created, no body sent

#### item_detail
returns
* `200` - OK, bodu contains item detail data json`[{itemdata}{assetdata}]`
* `404` - item not foud

### bin_order
Used for item creation and reordering.
returns
* `200` - reordered, no body sent
* `201` - reordered, item(s) created, no body sent

#### bin

#### rundown


