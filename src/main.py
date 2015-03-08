#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cgitb
cgitb.enable()

import typhoon.web


class MainHandler(typhoon.web.RequestHandler):
    def get(self):
        self.write('hello typhoon web framework')


class TestHandler(typhoon.web.RequestHandler):
    def get(self, idx):
        p = self.get_argument('page', '0')
        self.write('test handler\n')
        self.write('page=' + p)
        self.write('idx=' + idx)


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
