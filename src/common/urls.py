#!/usr/bin/env python
# -*- coding: utf-8 -*-

import handler.index
import handler.user
import handler.image

handlers = [
    (r"/", handler.index.MainHandler),

    # user
    (r"/user/login", handler.user.LoginHandler),
    (r"/user/register", handler.user.RegisterHandler),
    (r"/user/logout", handler.user.LogoutHandler),

    # image
    (r"/image/upload", handler.image.UploadHandler),
    (r"/image/manage", handler.image.ManageHandler),
    (r"/image/([0-9a-fA-F]{32})", handler.image.AccessHandlerV1),
    (r"/image/setavatar", handler.image.SetAvatarHandler),

    # about
    (r"/about", handler.index.AboutHandler),
]
