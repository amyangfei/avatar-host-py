#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base import BaseHandler
from common.utils import generate_salt, password_hash
from form.user import RegisterForm
from model.user import UserModel


class LoginHandler(BaseHandler):
    def get(self, **template_vars):
        self.render("user/login.html", **template_vars)

    def post(self, **template_vars):
        pass


class RegisterHandler(BaseHandler):
    def form_validate(self):
        pass

    def get(self, **template_vars):
        self.render("user/register.html", **template_vars)

    def post(self, **template_vars):
        form = RegisterForm(self)
        if not form.validate():
            errors = form.errors
            # error handling
            return self.render("user/register.html", errors=errors)

        username = form.get("username")
        email = form.get("email")
        password = form.get("password")

        salt = generate_salt(16)
        secure_password = password_hash(password, salt)

        user_model = UserModel()
        create_result = user_model.create_user(username=username, email=email,
                password=secure_password, salt=salt)

        from typhoon.log import app_log
        app_log.info("create_result: %d", create_result)

        """
        if create_result == 1:
            do_login(self, uid)
        """

        self.redirect("/")
