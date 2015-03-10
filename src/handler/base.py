#!/usr/bin/env python
# -*- coding: utf-8 -*-

import typhoon.web


class BaseHandler(typhoon.web.RequestHandler):
    def __init__(self, *argc, **kwargs):
        super(BaseHandler, self).__init__(*argc, **kwargs)

    def render(self, template_name, **template_vars):
        pass
