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
        self._cursor = None

    def _get_connection(self):
        return MySQLdb.Connect(
            host=self.host,
            port=self.port,
            user=self.user,
            passwd=self.password,
            db=self.dbname,
            charset='utf8'
        )

    def query(self, sql_stmt, params):
        cursor = self.conn.cursor()
        cursor.execute(sql_stmt, params)
        data = cursor.fetchall()
        cursor.close()
        return data

    def query_one(self, sql_stmt, params):
        cursor = self.conn.cursor()
        cursor.execute(sql_stmt, params)
        data = cursor.fetchone()
        cursor.close()
        return data

    def update(self, sql_stmt, params):
        cursor = self.conn.cursor()
        result = cursor.execute(sql_stmt, params)
        lastrowid = cursor.lastrowid
        self.conn.commit()
        cursor.close()
        return result, lastrowid

    def update_without_commit(self, sql_stmt, params):
        self._cursor = self._cursor or self.conn.cursor()
        result = self._cursor.execute(sql_stmt, params)
        lastrowid = self._cursor.lastrowid
        return result, lastrowid

    def commit(self):
        self.conn.commit()
        self._cursor.close()
        self._cursor = None
