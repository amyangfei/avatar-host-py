#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typhoon.web import RequestHandler
from typhoon.template import Loader, DirectorySource, default_parser


class BaseHandler(RequestHandler):
    def __init__(self, *argc, **kwargs):
        super(BaseHandler, self).__init__(*argc, **kwargs)
        self.template_loader = Loader(
            sources = [
                DirectorySource(self.application.settings.get("template_path")),
            ],
            parser = default_parser,
        )

    def render(self, template_name, **template_vars):
        html = self.render_string(template_name, **template_vars)
        return self.write(html)

    def render_string(self, template_name, **template_vars):
        template_vars.setdefault("errors", [])
        template_vars["request"] = self.request
        return self.template_loader.render(template_name, **template_vars)
