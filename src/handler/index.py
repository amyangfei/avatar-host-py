#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base import BaseHandler
from typhoon.log import app_log


class MainHandler(BaseHandler):
    def get(self):
        template_vars = {
            "test": "from typhoon cgi-based web framework"
        }
        return self.render("index/index.html", **template_vars)


class TestHandler(BaseHandler):
    def get(self, idx):
        self.write('test handler idx={}\n'.format(idx))

    def post(self, idx):
        name = self.get_argument('name', 'oooppps')
        pid = self.get_argument('pid', '0')
        app_log.info('post argument name=%s pid=%s', name, pid)
        self.write('receive name = {0} id = {1}\n'.format(name, pid))
