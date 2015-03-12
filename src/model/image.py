#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from model.base import BaseDAO


class ImageDAO(BaseDAO):
    def create_image(self, user_id, filename, md5_checksum):
        base_string = """INSERT INTO yagra.yagra_image
                    (user_id, filename, md5, created)
                    VALUES ({0}, '{1}', '{2}', '{3}')
                    """
        sql_string = base_string.format(user_id, filename, md5_checksum,
                time.strftime('%Y-%m-%d %H:%M:%S'))
        return self.db.update(sql_string)
