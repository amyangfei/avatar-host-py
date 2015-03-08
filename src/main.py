#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cgitb
cgitb.enable()

import typhoon.web
from typhoon.log import app_log


class MainHandler(typhoon.web.RequestHandler):
    def get(self):
        self.write('hello typhoon web framework')


class TestHandler(typhoon.web.RequestHandler):
    def get(self, idx):
        self.write('test handler idx={}\n'.format(idx))

    def post(self, idx):
        name = self.get_argument('name', 'oooppps')
        pid = self.get_argument('pid', '0')
        app_log.info('post argument name=%s pid=%s', name, pid)
        self.write('receive name = {0} id = {1}\n'.format(name, pid))


def main():
    settings = {
        'app_log': {
            'redirect_path': '/var/log/yagra/app.log',
            'log_level': 'DEBUG',
            'log_format_str': '%(asctime)s [%(levelname)s] %(pathname)s' \
                                ':%(lineno)s %(message)s',
        }
    }
    app = typhoon.web.Application([
        (r"/", MainHandler),
        (r"/regex/([0-9a-f]+)", TestHandler),
    ], **settings)
    app.run()


if __name__ == '__main__':
    main()
