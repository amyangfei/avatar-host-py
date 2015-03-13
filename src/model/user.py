#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import hashlib

from model.base import BaseDAO


class UserModel(object):
    def __init__(self, uid, username, email, created, password, salt, avatar):
        self.uid = uid
        self.username = username
        self.email = email
        self.created = created
        self.password = password
        self.salt = salt
        self.avatar = avatar

    def get_avatar_url(self):
        email_md5 = hashlib.md5(self.email).hexdigest()
        return "/image/" + email_md5


class UserDAO(BaseDAO):
    def create_user(self, username, email, password, salt):
        # TODO: security detection, such as SQL injection
        base_string = """INSERT INTO yagra_user
                    (username, email, password, salt, created)
                    VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')
                    """
        sql_string = base_string.format(username, email, password, salt,
                time.strftime('%Y-%m-%d %H:%M:%S'))
        return self.db.update(sql_string)

    def get_user_by_one_unique_filed(self, field_name, field_value):
        base_string = """SELECT uid, username, email, password,
                    salt, created, avatar
                    FROM yagra_user where {0} = '{1}'
                    """
        sql_string = base_string.format(field_name, field_value)
        raw = self.db.query_one(sql_string)
        if raw:
            uid, username, email, password, salt, created, avatar = raw
            return UserModel(
                uid = uid,
                username = username,
                email = email,
                password = password,
                salt = salt,
                created = created,
                avatar = avatar,
            )
        return raw

    def get_user_by_email(self, email):
        return self.get_user_by_one_unique_filed("email", email)

    def get_user_by_uid(self, uid):
        return self.get_user_by_one_unique_filed("uid", uid)

    def set_user_avatar(self, uid, avatar_id):
        base_string = """UPDATE yagra_user
                    SET avatar = {0} WHERE uid = {1}
                    """
        sql_string = base_string.format(avatar_id, uid)
        return self.db.update(sql_string)
