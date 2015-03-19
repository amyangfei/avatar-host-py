#!/bin/bash

scriptdir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
project=yagra
sep="----------------------------------------------------"
red='\e[0;31m'
NC='\e[0m' # No Color

clean_old_containers_and_images() {
    sudo docker stop yagra-apache yagra-mysql yagra-nginx
    sudo docker rm yagra-apache yagra-mysql yagra-nginx
    sudo docker rmi yagra/apache yagra/mysql yagra/db_scheme_loader yagra/nginx
}


build_images() {
    cd $scriptdir
    sudo ./mkmysql.sh

    cd $scriptdir
    sudo ./mkapache_cgi.sh

    cd $scriptdir
    sudo ./mkdb_scheme_loader.sh

    cd $scriptdir
    sudo ./mknginx.sh
}


# TODO: use docker volume for log, upload images and db data storage.
# But still have unsolved problem as non-root user can't write to shared.
# Some references: https://github.com/boot2docker/boot2docker/issues/581
# https://github.com/docker/docker/issues/7198
# https://github.com/docker/docker/issues/3124
start_containers() {
    sudo docker run --name "yagra-mysql" -h "yagra-mysql" -d \
        -e MYSQL_ROOT_PASSWORD=root -e MYSQL_USER=yagra \
        -e MYSQL_PASSWORD=yagra -e MYSQL_DATABASE=yagra yagra/mysql

    sudo docker run --name "yagra-apache" -h "yagra-apache" -d \
        --link yagra-mysql:yagra-mysql yagra/apache

    # wait for mysql start up
    sudo docker run --rm=true --name "yagra-db_scheme_loader" \
        -h "yagra-db_scheme_loader" -e MYSQL_USER=yagra \
        -e MYSQL_PASSWORD=yagra -e MYSQL_DATABASE=yagra \
        --link yagra-mysql:yagra-mysql yagra/db_scheme_loader

    sudo docker run --name "yagra-nginx" -h "yagra-nginx" -d -p 80:80 \
        --link yagra-apache:yagra-apache yagra/nginx
}

remove_containers() {
    echo "remove all yagra containers..."
    sudo docker stop yagra-apache yagra-mysql yagra-nginx
    sudo docker rm yagra-apache yagra-mysql yagra-nginx
}

show_help() {
    echo "Usage:"
    echo ${sep}

    echo -e "${red}clear${NC} all ${project} docker containers"
    echo example: "$0 clear"
    echo ""

    echo -e "${red}drop${NC} all ${project} docker images"
    echo example: "$0 drop"
    echo ""

    echo -e "${red}start${NC} fresh containers without rebuilding images"
    echo example: "$0 start"
    echo ""

    echo -e "${red}clean-start${NC} fresh containers after rebuilding all images"
    echo example: "$0 clean-start"
    echo ""

    echo ${sep}
    exit 1
}

case "$1" in
    clear)
        shift 1
        remove_containers $*
        ;;
    drop)
        shift 1
        clean_old_containers_and_images $*
        ;;
    start)
        shift 1
        remove_containers $*
        start_containers $*
        ;;
    clean-start)
        clean_old_containers_and_images $*
        build_images $*
        start_containers $*
        shift 1
        ;;
    *)
        show_help $*
        ;;
esac
exit 0
