#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from model.user import UserDAO

RE_USERNAME = re.compile("^[a-zA-Z][a-zA-Z0-9_]{2,19}$")

# not quite complete enough, doesn't support hello@bla-bla.com etc.
RE_EMAIL = re.compile(r"^[_A-Za-z0-9-\+]+(\.[_A-Za-z0-9-]+)*@[A-Za-z0-9-]+(\.[A-Za-z0-9]+)*(\.[A-Za-z]{2,})$")

PASS_MIN_LEN = 3
PASS_MAX_LEN = 32


class FormNotVaidateError(Exception):
    pass


class BaseForm(object):
    def __init__(self, request_handler):
        self.handler = request_handler
        self.validated = False
        self.fields = {}
        self.errors = []

    def get(self, name):
        if not self.validated:
            raise FormNotVaidateError
        return self.fields.get(name)

    def get_argument(self, name, default=None):
        return self.handler.get_argument(name, None)

    def validate(self):
        raise NotImplementedError


class RegisterForm(BaseForm):

    def validate(self):
        # check username pattern
        username = self.get_argument("username")
        if username is None:
            self.errors.append("必须填写用户名")
        elif not RE_USERNAME.match(username):
            self.errors.append("非法的用户名")

        # check email pattern
        email = self.get_argument("email")
        if email is None:
            self.errors.append("必须填写 email 地址")
        elif not RE_EMAIL.match(email):
            self.errors.append("非法的 email 地址")

        # check password length and equality of two password input
        password = self.get_argument("password")
        if password is None:
            self.errors.append("必须填写密码")
        elif len(password) < PASS_MIN_LEN:
            self.errors.append("密码长度过短")
        elif len(password) > PASS_MAX_LEN:
            self.errors.append("密码长度过长")
        password_confirm = self.get_argument("password_confirm")
        if password_confirm is None:
            self.errors.append("必须填写确认密码")
        elif password != None and password != password_confirm:
            self.errors.append("两次输入密码不一致")

        self.validated = True
        self.fields["username"] = username
        self.fields["email"] = email
        self.fields["password"] = password

        # validations above don't require to connect to DB, so we check them first.
        if len(self.errors) > 0:
            return False

        # check the uniqueness of email
        user_dao = UserDAO(self.handler.get_db_config())
        if user_dao.get_user_by_email(email.lower()):
            self.errors.append("该邮箱已经被使用！")

        return False if len(self.errors) > 0 else True


class LoginForm(BaseForm):
    def validate(self):
        email = self.get_argument("email")
        if email is None:
            self.errors.append("必须填写您的 email 地址")

        password = self.get_argument("password")
        if password is None:
            self.errors.append("请填写密码")

        self.validated = True
        self.fields["email"] = email
        self.fields["password"] = password

        return False if len(self.errors) > 0 else True
