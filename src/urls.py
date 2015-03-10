#!/usr/bin/env python
# -*- coding: utf-8 -*-

import handler.index

handlers = [
    (r"/", handler.index.MainHandler),
    (r"/regex/([0-9a-f]+)", handler.index.TestHandler),
]
