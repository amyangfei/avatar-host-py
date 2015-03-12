#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cgitb
cgitb.enable()

import os

from common.urls import handlers
from typhoon.web import Application


def main():
    settings = {
        'app_log': {
            'redirect_path': '/var/log/yagra/app.log',
            'log_level': 'DEBUG',
            'log_format_str': '%(asctime)s [%(levelname)s] %(pathname)s' \
                                ':%(lineno)s %(message)s',
        },
        'template_path': os.path.join(os.path.dirname(__file__), "templates"),
        'static_path': os.path.join(os.path.dirname(__file__), "static"),
        'secure_key': "A0j*fCdxi#&vn5Ly",
        'session_timeout': 86400 * 15,
    }
    # TODO: Load more config from config file
    settings['upload_path'] = '/var/www/yagra/upload'
    app = Application(handlers, **settings)
    app.run()


if __name__ == '__main__':

    main()
