#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base import BaseHandler, get_session, prepare_session
from common.utils import generate_salt, password_hash
from form.user import RegisterForm, LoginForm
from model.user import UserDAO

from typhoon.log import app_log


def do_login(request_handler, user):
    app_log.debug("user login email=%s", user.email)
    request_handler.session = get_session(request_handler)
    request_handler.session["uid"] = user.uid
    request_handler.session["username"] = user.username
    request_handler.session["email"] = user.email
    request_handler.session.save()
    request_handler.set_secure_cookie("magic_id", str(user.uid))


class LoginHandler(BaseHandler):
    def get(self, **template_vars):
        self.render("user/login.html", **template_vars)

    def post(self, **template_vars):
        form = LoginForm(self)
        if not form.validate():
            errors = form.errors
            return self.get(errors=errors)

        email = form.get("email")
        password = form.get("password")

        user_dao = UserDAO(self.get_db_config())
        user_info = user_dao.get_user_by_email(email)

        if user_info is None:
            errors = ["email 地址不存在"]
            return self.get(errors=errors)

        secure_password = password_hash(password, user_info.salt)
        if secure_password != user_info.password:
            errors = ["密码不正确"]
            return self.get(errors=errors)

        do_login(self, user_info)
        self.redirect(self.get_argument("next", "/"))


class LogoutHandler(BaseHandler):
    def do_logout(self):
        self.session.clear()
        self.clear_all_cookies()

    @prepare_session
    def get(self):
        self.do_logout()
        self.redirect(self.get_argument("next", "/"))


class RegisterHandler(BaseHandler):
    def get(self, **template_vars):
        self.render("user/register.html", **template_vars)

    def post(self, **template_vars):
        form = RegisterForm(self)
        if not form.validate():
            errors = form.errors
            return self.render("user/register.html", errors=errors)

        username = form.get("username")
        email = form.get("email")
        password = form.get("password")

        salt = generate_salt(16)
        secure_password = password_hash(password, salt)

        user_dao = UserDAO(self.get_db_config())
        create_result = user_dao.create_user(username=username, email=email,
                password=secure_password, salt=salt)

        if create_result == 1:
            app_log.info("new user registered successfully email=%s", email)
            user = user_dao.get_user_by_email(email)
            if user:
                do_login(self, user)
            else:
                app_log.error("Failed to retrive user, email=%s", email)

        self.redirect("/")
