#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common.db import DB


class BaseDAO(object):
    def __init__(self):
        super(BaseDAO, self).__init__()
        # TODO: read db params from config file
        self.db = DB(host='localhost', port=3306, user='yagra',
                password='yagra', dbname='yagra')
