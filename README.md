nx.server
=========

## About

OpenNX media asset management core. Complete rewrite of Nebula project.

Early pre-alpha version - Only to be used in presence of developers.

### New core features
* EBUCore Compliant. 
* Simplified HTTPS-Based API 
* FIMS Support for 3rd party integration - when someone writes useable specs
* Multilanguage support for UI and metadata
* Deployment and updates via Puppet
* Hive-side seismic message queue for outsiders
* Metadata tags aliases and grouping (genre for music and movies in one column)

### Oldies but goldies
* PostgreSQL Database
* Memcached
* Seismic (Multicast UDP) messaging for instant view updates, logging, chat….


## Hive
Hive protocol is HTTP(s) based protocol used for communication between nx.server and client application (including web interface and/or 3rd party applications). Hive should also serve as playout control proxy (optional).

### Generic responses

* `400` - Bad request, query is malformed
* `401` - Unauthorised. Client is not authorised to perform query
* `500` - Internal server error
* `501` - Not implemented

### Methods


#### browse
returns
* `200` - OK, body contains search result
* `203` - OK, partial information. There are more matching assets than can be displayed.
* `204` - OK, no result, no body sent

#### asset_detail
returns
* `200` - OK, bodu contains asset detail data
* `404` - asset not foud

#### new_asset
returns
* `201` - created, no body sent

#### item_detail
returns
* `200` - OK, bodu contains item detail data
* `404` - asset not foud

### new_item
returns
* `201` - created, no body sent

bin

rundown


