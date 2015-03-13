#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from model.base import BaseDAO


class ImageModel(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def get_url(self):
        return "/upload/" + getattr(self, "filename")


class ImageDAO(BaseDAO):
    # FIXME: access to both yagra_image table and yagra_user table
    def create_image(self, user_id, filename, md5_checksum, email_md5,
            update_avatar):
        base_string = """INSERT INTO yagra.yagra_image
                    (user_id, filename, md5, created, email_md5)
                    VALUES ({0}, '{1}', '{2}', '{3}', '{4}')
                    """
        sql_string = base_string.format(user_id, filename, md5_checksum,
                time.strftime('%Y-%m-%d %H:%M:%S'), email_md5)
        update_base_string = """UPDATE yagra.yagra_user
                    SET avatar = {0} where uid = {1}"""
        if not update_avatar:
            return self.db.update(sql_string)
        else:
            _, lastrowid = self.db.update_without_commit(sql_string)
            sql_string = update_base_string.format(lastrowid, user_id)
            result, lastrowid = self.db.update_without_commit(sql_string)
            self.db.commit()
            return result, lastrowid

    def get_image_by_uid_and_md5(self, user_id, md5_checksum):
        base_string = """
                    SELECT imgid, user_id, filename, created, md5, email_md5
                    FROM yagra.yagra_image
                    WHERE user_id = {0} and md5 = '{1}'
                    """
        sql_string = base_string.format(user_id, md5_checksum)
        raw = self.db.query_one(sql_string)
        if raw:
            imgid, user_id, filename, created, md5, email_md5 = raw
            imgid, user_id, filename, created, md5, email_md5 = raw
            return ImageModel(imgid=imgid, user_id=user_id, filename=filename,
                    created=created, md5=md5, email_md5=email_md5,)
        return None

    def get_image_by_emailmd5(self, email_md5):
        base_string = """
                SELECT imgid, user_id, filename, created, md5, email_md5
                FROM yagra.yagra_image
                where email_md5 = '{0}'
                """
        sql_string = base_string.format(email_md5)
        raw = self.db.query_one(sql_string)
        if raw:
            imgid, user_id, filename, created, md5, email_md5 = raw
            return ImageModel(imgid=imgid, user_id=user_id, filename=filename,
                    created=created, md5=md5, email_md5=email_md5,)
        return None

    def get_own_image_count(self, user_id):
        base_string = """SELECT COUNT(*) FROM yagra.yagra_image
                WHERE user_id = {0}"""
        sql_string = base_string.format(user_id)
        raw = self.db.query_one(sql_string)
        return 0 if raw is None else raw[0]

    def get_own_images(self, user_id, offset=0, limit=10):
        base_string = """
                SELECT imgid, user_id, filename, created, email_md5, md5
                FROM yagra.yagra_image WHERE imgid >=
                    (SELECT imgid FROM yagra.yagra_image
                    WHERE user_id={0} ORDER BY imgid LIMIT {1}, 1)
                LIMIT {2}
                """
        sql_string = base_string.format(user_id, offset, limit)
        raw = self.db.query(sql_string)
        images = []
        if raw:
            for row in raw:
                imgid, user_id, filename, created, md5, email_md5 = row
                images.append(ImageModel(imgid=imgid, user_id=user_id,
                    filename=filename, created=created, md5=md5,
                    email_md5=email_md5,)
                )
        return images
