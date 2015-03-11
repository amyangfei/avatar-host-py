#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base import BaseHandler, get_session
from common.utils import generate_salt, password_hash
from form.user import RegisterForm
from model.user import UserModel

from typhoon.log import app_log


class LoginHandler(BaseHandler):
    def get(self, **template_vars):
        self.render("user/login.html", **template_vars)

    def post(self, **template_vars):
        pass


class LogoutHandler(BaseHandler):
    def do_logout(self):
        # TODO: destroy sessions
        # TODO: destroy cookies
        pass

    def get(self):
        self.do_logout()
        self.redirect(self.get_argument("next"), "/")


class RegisterHandler(BaseHandler):
    def form_validate(self):
        pass

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

        user_model = UserModel()
        create_result = user_model.create_user(username=username, email=email,
                password=secure_password, salt=salt)

        if create_result == 1:
            app_log.info("new user registered successfully email=%s", email)
            user = user_model.get_user_by_email(email)
            if user:
                self.do_login(user)
            else:
                app_log.error("Failed to retrive user, email=%s", email)

        self.redirect("/")

    def do_login(self, user):
        app_log.debug("user login email=%s", user.get("email"))
        self.session = get_session(self)
        self.session["uid"] = user["uid"]
        self.session["username"] = user["username"]
        self.session["email"] = user["email"]
        self.session.save()
        self.set_secure_cookie("magicid", str(user["uid"]))
