#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base import BaseHandler
from typhoon.log import app_log


class MainHandler(BaseHandler):
    def get(self):
        template_vars = {
            "test": "from typhoon cgi-based web framework",
            "active_page": "home",
        }
        return self.render("index/index.html", **template_vars)


class AboutHandler(BaseHandler):
    def get(self):
        template_vars = {
            "active_page": "about",
            "api_url": "http://{0}/image".format(self.request.host),
        }
        return self.render("index/about.html", **template_vars)
