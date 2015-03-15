#!/bin/bash

if [ ! -f ./conf/mysql_my.cnf ]; then
    echo "my.cnf not found"
    exit 1
fi

if [ ! -f ../deploy/yagra_scheme.sql ]; then
    echo "../deploy/yagra_scheme.sql not found"
    exit 1
fi

cd .. || exit $?

docker rmi yagra/mysql

cat > Dockerfile <<EOF
FROM mysql:5.6

ENV CNFDIR /etc/mysql
ENV DATADIR /data/mysql

RUN mkdir -p \${CNFDIR}
RUN mkdir -p \${CNFDIR}/conf.d/
RUN mkdir -p \${DATADIR}

ADD ./docker/conf/mysql_my.cnf \${CNFDIR}/my.cnf
ADD ./deploy/yagra_scheme.sql \${DATADIR}/yagra_scheme.sql

RUN chown -R mysql:mysql \${CNFDIR}
RUN chown -R mysql:mysql \${DATADIR}

EOF

docker build --force-rm -t yagra/mysql . && rm -f Dockerfile

# start a container
# sudo docker run --name "yagra-mysql" -h "yagra-mysql" -d -p 3006:3306 \
#    -e MYSQL_ROOT_PASSWORD=root -e MYSQL_USER=yagra -e MYSQL_PASSWORD=yagra -e MYSQL_DATABASE=yagra yagra/mysql

# connect to mysql
# sudo docker run -it --link yagra-mysql:yagra-mysql --rm mysql sh -c 'exec mysql -hyagra-mysql -P3306 -uroot -p'

# import database structure
# mysql -u yagra -p --database=yagra < yagra_scheme.sql
