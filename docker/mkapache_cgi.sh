#!/bin/bash

if [ ! -f ./conf/apache_yagra.conf ]; then
    echo "apache_yagra.conf not found"
    exit 1
fi

docker rmi yagra/apache

cat > Dockerfile <<EOF
FROM debian:wheezy

# upgrade & install required packages
RUN apt-get update
RUN apt-get install -y git apache2 python python-dev libmysqlclient-dev python-pip
RUN pip install mysql-python

ENV APACHE_RUN_USER www-data
ENV APACHE_RUN_GROUP www-data
ENV APACHE_LOG_DIR /var/log/apache2
ENV APACHE_CONF_DIR /etc/apache2

ENV TMPDIR /tmp
ENV WEBBASE /var/www/yagra
ENV APPLOG /var/log/yagra
ENV UPLOAD /var/www/yagra/upload

RUN mkdir -p \${TMPDIR} \${WEBBASE} \${APPLOG} \${UPLOAD}

WORKDIR \${TMPDIR}
RUN git clone https://github.com/amyangfei/avatar-host-py
RUN cp -r avatar-host-py/src/* \${WEBBASE}
WORKDIR \${WEBBASE}
RUN cp config.py.example config.py

ADD ./conf/apache_yagra.conf \${APACHE_CONF_DIR}/sites-available/yagra.conf
RUN ln -s \${APACHE_CONF_DIR}/sites-available/yagra.conf \${APACHE_CONF_DIR}/sites-enabled/yagra.conf

RUN chown -R www-data:www-data \${WEBBASE} \${APPLOG} \${UPLOAD}

# enable apache cgi module
RUN a2enmod cgi
# enable apache url rewrite
RUN a2enmod rewrite

EXPOSE 80

CMD ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]

EOF

docker build --force-rm -t yagra/apache . && rm -f Dockerfile

# start a container
# sudo docker run --name "yagra-apache" -h "yagra-apache" -d -p 8001:80 --link yagra-mysql:yagra-mysql yagra/apache

