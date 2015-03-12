#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from model.base import BaseDAO


class ImageModel(object):
    def __init__(self, user_id, filename, md5, created):
        self.user_id = user_id
        self.filename = filename
        self.md5 = md5
        self.created = created


class ImageDAO(BaseDAO):
    def create_image(self, user_id, filename, md5_checksum):
        base_string = """INSERT INTO yagra.yagra_image
                    (user_id, filename, md5, created)
                    VALUES ({0}, '{1}', '{2}', '{3}')
                    """
        sql_string = base_string.format(user_id, filename, md5_checksum,
                time.strftime('%Y-%m-%d %H:%M:%S'))
        return self.db.update(sql_string)

    def get_image_by_uid_and_md5(self, user_id, md5_checksum):
        base_string = """SELECT user_id, filename, created, md5
                    FROM yagra.yagra_image
                    WHERE user_id = {0} and md5 = '{1}'
                    """
        sql_string = base_string.format(user_id, md5_checksum)
        raw = self.db.query_one(sql_string)
        if raw:
            user_id, filename, created, md5 = raw
            return ImageModel (
                user_id = user_id,
                filename = filename,
                created = created,
                md5 = md5,
            )
        return None
