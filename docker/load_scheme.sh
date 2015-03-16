#!/bin/bash

MYSQL_PORT=3306

while true; do
    port_test=$(nc -vz yagra-mysql $MYSQL_PORT 2>&1|grep "Connection refused")
    if [ "$port_test" != "" ]; then
        echo "$(date) - waiting for mysql start up..."
        sleep 1
    else
        echo "Connection with yagra-mysql $MYSQL_PORT successfully..."
        break
    fi
done

cd /root
mysql -h yagra-mysql -u $MYSQL_USER -p$MYSQL_PASSWORD --database=$MYSQL_DATABASE < yagra_scheme.sql
