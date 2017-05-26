#!/bin/bash
BASEDIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )


chmod 755 services

find $BASEDIR/services -type d -exec chmod 775 {} +
find $BASEDIR/services -type f -exec chmod 664 {} +

find $BASEDIR/admin -type d -exec chmod 775 {} +
find $BASEDIR/admin -type f -exec chmod 664 {} +

find $BASEDIR/nx -type d -exec chmod 775 {} +
find $BASEDIR/nx -type f -exec chmod 664 {} +

