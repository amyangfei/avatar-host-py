#!/usr/bin/env python
# -*- coding: utf-8 -*-

import handler.index
import handler.user
import handler.image

handlers = [
    (r"/", handler.index.MainHandler),
    (r"/regex/([0-9a-f]+)", handler.index.TestHandler),

    # user
    (r"/user/login", handler.user.LoginHandler),
    (r"/user/register", handler.user.RegisterHandler),
    (r"/user/logout", handler.user.LogoutHandler),

    # image
    (r"/image/upload", handler.image.UploadHandler),
]
