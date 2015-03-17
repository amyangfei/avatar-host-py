#!/bin/bash

scriptdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

clean_old_containers_and_images() {
    sudo docker stop yagra-apache yagra-mysql
    sudo docker rm yagra-apache yagra-mysql
    sudo docker rmi yagra/apache yagra/mysql yagra/db_scheme_loader
}


build_images() {
    cd $scriptdir
    sudo ./mkmysql.sh

    cd $scriptdir
    sudo ./mkapache_cgi.sh

    cd $scriptdir
    sudo ./mkdb_scheme_loader.sh
}


# TODO: use docker volume for log, upload images and db data storage.
# But still have unsolved problem as non-root user can't write to shared.
# Some references: https://github.com/boot2docker/boot2docker/issues/581
# https://github.com/docker/docker/issues/7198
# https://github.com/docker/docker/issues/3124
start_containers() {
    sudo docker run --name "yagra-mysql" -h "yagra-mysql" -d -p 3006:3306 \
        -e MYSQL_ROOT_PASSWORD=root -e MYSQL_USER=yagra \
        -e MYSQL_PASSWORD=yagra -e MYSQL_DATABASE=yagra yagra/mysql

    sudo docker run --name "yagra-apache" -h "yagra-apache" -d -p 8001:80 \
        --link yagra-mysql:yagra-mysql yagra/apache

    # wait for mysql start up
    sudo docker run --rm=true --name "yagra-db_scheme_loader" \
        -h "yagra-db_scheme_loader" -e MYSQL_USER=yagra \
        -e MYSQL_PASSWORD=yagra -e MYSQL_DATABASE=yagra \
        --link yagra-mysql:yagra-mysql yagra/db_scheme_loader

}

clean_old_containers_and_images $*
build_images $*
start_containers $*
