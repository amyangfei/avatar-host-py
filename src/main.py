#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cgitb
cgitb.enable()

import os

from urls import handlers
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
    }
    app = Application(handlers, **settings)
    app.run()


if __name__ == '__main__':

    main()
