#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb


def singleton(cls, *args, **kw):
    instances = {}
    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton


@singleton
class DB():
    def __init__(self, host, port, user, password, dbname):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.dbname = dbname

        self.conn = self._get_connection()

    def _get_connection(self):
        return MySQLdb.Connect(
            host = self.host,
            port = self.port,
            user = self.user,
            passwd = self.password,
            db = self.dbname,
            charset = 'utf8'
        )

    def query(self, sql_string):
        cursor = self.conn.cursor()
        cursor.execute(sql_string)
        data = cursor.fetchall()
        cursor.close()
        return data

    def update(self, sql_string):
        cursor = self.conn.cursor()
        result = cursor.execute(sql_string)
        self.conn.commit()
        cursor.close()
        return result
