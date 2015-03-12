#!/bin/bash

cur=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
dst=/var/www/yagra
log=/var/log/yagra/app.log

sudo rsync -av --progress --delete --exclude \*.pyc --exclude upload/ $cur/../src/ $dst
if [ ! -f $log ]; then
    touch $log
    chown www-data:www-data $log
fi
