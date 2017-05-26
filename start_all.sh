#!/bin/bash
#
# This script starts nebula server and web interface in screen.
# Use crontab -e and add following line to start it after reboot.
#
# @reboot /opt/stream/start_all.sh
#


PATH=/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH

cd /opt/nx.server

echo "Starting nebula"

screen -AdmS nebula -t Nebula python "nebula.py"
screen -S nebula -X screen -t Admin python "run_admin.py"

