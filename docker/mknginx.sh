#!/bin/bash

if [ ! -f ./conf/nginx.conf ]; then
    echo "./conf/nginx.conf not found"
    exit 1
fi

if [ ! -f ./conf/nginx_yagra.conf ]; then
    echo "./conf/nginx_yagra.conf not found"
    exit 1
fi

cat > Dockerfile <<EOF
FROM nginx:1.7

ENV HOMEDIR /home/yagra
ENV LOGDIR \${HOMEDIR}/var/log/nginx
RUN mkdir -p \${HOMEDIR} \${LOGDIR}
RUN groupadd -r yagra && useradd -r -g yagra yagra -s /bin/bash -d \${HOMEDIR}
RUN echo 'yagra:yagra' | chpasswd

# copy nginx config file
ADD ./conf/nginx.conf /etc/nginx/nginx.conf
ADD ./conf/nginx_yagra.conf /etc/nginx/sites-enabled/yagra.conf

RUN chown -R yagra:yagra \${HOMEDIR}

EXPOSE 80

EOF

docker build --force-rm -t yagra/nginx . && rm -f Dockerfile

# sudo docker run --name "yagra-nginx" -h "yagra-nginx" -d -p 80:80 \
#    --link yagra-apache:yagra-apache yagra/nginx
