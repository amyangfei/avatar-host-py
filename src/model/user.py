#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from common.db import DB


class BaseModel(object):
    def __init__(self):
        super(BaseModel, self).__init__()
        # TODO: read db params from config file
        self.db = DB(host='localhost', port=3306, user='yagra',
                password='yagra', dbname='yagra')


class UserModel(BaseModel):
    def create_user(self, username, email, password, salt):
        # TODO: security detection, such as SQL injection
        base_string = """INSERT INTO yagra.yagra_user
                    (username, email, password, salt, created)
                    VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')
                    """
        sql_string = base_string.format(username, email, password, salt,
                time.strftime('%Y-%m-%d %H:%M:%S'))
        return self.db.update(sql_string)

    def get_user_by_one_unique_filed(self, field_name, field_value):
        base_string = """SELECT uid, username, email, password, salt, created
                    FROM yagra.yagra_user where {0} = '{1}'
                    """
        sql_string = base_string.format(field_name, field_value)
        raw = self.db.query_one(sql_string)
        if raw:
            uid, username, email, password, salt, created = raw
            return dict(
                uid = uid,
                username = username,
                email = email,
                password = password,
                salt = salt,
                created = created,
            )
        return raw

    def get_user_by_email(self, email):
        return self.get_user_by_one_unique_filed("email", email)

    def get_user_by_uid(self, uid):
        return self.get_user_by_one_unique_filed("uid", uid)
