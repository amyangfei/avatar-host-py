#!/bin/bash

if [ ! -f ../deploy/yagra_scheme.sql ]; then
    echo "../deploy/yagra_scheme.sql not found"
    exit 1
fi

cd .. || exit $?

docker rmi yagra/db_scheme_loader

cat > Dockerfile <<EOF
FROM debian:wheezy

# upgrade & install required packages
RUN apt-get update
RUN apt-get install -y mysql-client

WORKDIR /root
ADD ./deploy/yagra_scheme.sql /root/yagra_scheme.sql
ADD ./docker/load_scheme.sh /root/load_scheme.sh

CMD [ "/bin/sh", "-c", "/root/load_scheme.sh" ]

EOF

docker build --force-rm -t yagra/db_scheme_loader . && rm -f Dockerfile

# start a container
# sudo docker run --rm=true --name "yagra-db_scheme_loader" -h "yagra-db_scheme_loader" \
#   -e MYSQL_USER=yagra -e MYSQL_PASSWORD=yagra -e MYSQL_DATABASE=yagra  \
#   --link yagra-mysql:yagra-mysql yagra/db_scheme_loader

