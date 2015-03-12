#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import wraps

from common.session import Session, SessionManager, MySQLStore
from model.user import UserDAO
from typhoon.web import RequestHandler
from typhoon.template import Loader, DirectorySource, default_parser
from common.db import DB


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
        template_vars.setdefault("notify", [])
        template_vars["request"] = self.request
        template_vars["current_user"] = self.current_user
        return self.template_loader.render(template_name, **template_vars)

    def get_login_url(self):
        return "/user/login"

    def get_current_user(self):
        uid = self.get_secure_cookie("magic_id")
        if not uid:
            return None
        user_dao = UserDAO(self.get_db_config())
        return user_dao.get_user_by_uid(uid)

    def get_db_config(self):
        return self.application.settings.get("db")


"""As our program only runs one time when a cgi request comes, we dont't need to
keep a resident session manager. We only create session manager if we needed as
creating and destroying a db connection is quite excessive.
"""
def get_session(request_handler):
    db_config = request_handler.get_db_config()
    db = DB(
        host = db_config["host"],
        port = db_config["port"],
        user = db_config["user"],
        password = db_config["password"],
        dbname = db_config["dbname"],
    )
    data_store = MySQLStore(db)
    session_manager = SessionManager(
            request_handler.application.settings.get('secure_key'), data_store,
            request_handler.application.settings.get('session_timeout'))
    return Session(session_manager, request_handler)


def prepare_session(method):
    """Decorate methods with this when we use session in the method."""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        assert isinstance(self, RequestHandler)
        self.session = get_session(self)
        return method(self, *args, **kwargs)
    return wrapper
