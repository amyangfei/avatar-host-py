#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.db import DB


class BaseDAO(object):

    def __init__(self, db_config):
        super(BaseDAO, self).__init__()
        self.db = DB(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
            dbname=db_config["dbname"],
        )
