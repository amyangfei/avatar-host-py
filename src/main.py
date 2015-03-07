#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cgitb
cgitb.enable()

import typhoon.web


class MainHandler(typhoon.web.RequestHandler):
    def get(self):
        self.write('hello typhoon web framework')


def main():
    app = typhoon.web.Application([
        (r"/", MainHandler),
    ])
    app.run()


if __name__ == '__main__':
    main()
