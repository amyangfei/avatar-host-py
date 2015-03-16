#!/bin/bash

cd /root
mysql -h yagra-mysql -u $MYSQL_USER -p$MYSQL_PASSWORD --database=$MYSQL_DATABASE < yagra_scheme.sql
