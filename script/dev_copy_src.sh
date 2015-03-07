#!/bin/bash

cur=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
dst=/var/www/yagra

sudo rsync -av --progress --delete --exclude \*.pyc $cur/../src/ $dst
sudo chown -R root:root $dst
sudo touch $dst/debug.log
sudo chmod a+w $dst/debug.log
