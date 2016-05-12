Nebula
======
_Version 4.25_

Nebula is media asset management and workflow automation system for TV and radio broadcast.

Nebula profits from several great open source projects such as [ffmpeg](http://www.ffmpeg.org) and [CasparCG](http://www.casparcg.com)
and provides (almost) complete toolset for:

 - signal, stream and file based ingest
 - media asset management, metadata handling
 - conversion, video and audio normalization (incl. EBU R128)
 - programme planning, scheduling
 - playout control
 - dynamic CG
 - web publishing
 - statistics

Documentation
------------

See [wiki](https://github.com/opennx/nx.server/wiki/)



Installation
------------

Nebula requires Debian Jessie.

### Base node
```bash
apt-get install git python-psycopg2 python-pylibmc cifs-utils screen ntp
cd /opt/ && git clone https://github.com/opennx/installers
cd /opt/ && git clone https://github.com/opennx/nx.server
cd /opt/nx.server && ./vendor.sh
```

### DB Server
```
cd /opt/installers && ./install.postgres.sh
```

### Core Server

```bash
cd /opt/installers && ./install.nginx.sh

```

### Media processing node

```bash
cd /opt/installers && ./install.ffmpeg.sh
```

### Node configuration

```
cd /opt/nx.server
vim local_settings.json
```
