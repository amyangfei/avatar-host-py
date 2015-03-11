#!/usr/bin/env python
# -*- coding: utf-8 -*-

import handler.index
import handler.user

handlers = [
    (r"/", handler.index.MainHandler),
    (r"/regex/([0-9a-f]+)", handler.index.TestHandler),

    # user
    (r"/user/login", handler.user.LoginHandler),
    (r"/user/register", handler.user.RegisterHandler),
    (r"/user/logout", handler.user.LogoutHandler),
]
