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
        insert_sql_stmt = """INSERT INTO yagra_image
                    (user_id, filename, md5, created, email_md5)
                    VALUES (%s, %s, %s, %s, %s)
                    """
        insert_params = (
            user_id,
            filename,
            md5_checksum,
            time.strftime('%Y-%m-%d %H:%M:%S'),
            email_md5)
        update_sql_stmt = """UPDATE yagra_user
                    SET avatar = %s where uid = %s"""
        if not update_avatar:
            return self.db.update(insert_sql_stmt, insert_params)
        else:
            _, lastrowid = self.db.update_without_commit(insert_sql_stmt,
                                                         insert_params)
            update_params = (lastrowid, user_id)
            result, lastrowid = self.db.update_without_commit(
                update_sql_stmt, update_params)
            self.db.commit()
            return result, lastrowid

    def update_user_avatar(self, user_id, imgid, email_md5):
        # set old avatar linked email_md5 to empty string
        unlink_stmt = """UPDATE yagra_image SET email_md5 = ''
                WHERE email_md5 = %s"""
        unlink_params = (email_md5, )
        self.db.update_without_commit(unlink_stmt, unlink_params)

        # set new avatar linked with email_md5
        link_stmt = """UPDATE yagra_image SET email_md5 = %s
                WHERE imgid = %s"""
        link_params = (email_md5, imgid)
        self.db.update_without_commit(link_stmt, link_params)

        avatar_stmt = """UPDATE yagra_user SET avatar = %s
                WHERE uid = %s"""
        avatar_params = (imgid, user_id)
        self.db.update_without_commit(avatar_stmt, avatar_params)

        self.db.commit()

    def get_image_by_id(self, image_id):
        sql_stmt = """
                SELECT imgid, user_id, filename, created, md5, email_md5
                FROM yagra_image
                WHERE imgid = %s
                """
        params = (image_id, )
        raw = self.db.query_one(sql_stmt, params)
        if raw:
            imgid, user_id, filename, created, md5, email_md5 = raw
            return ImageModel(imgid=imgid, user_id=user_id, filename=filename,
                              created=created, md5=md5, email_md5=email_md5,)
        return None

    def get_image_by_uid_and_md5(self, user_id, md5_checksum):
        sql_stmt = """
                    SELECT imgid, user_id, filename, created, md5, email_md5
                    FROM yagra_image
                    WHERE user_id = %s and md5 = %s
                    """
        params = (user_id, md5_checksum)
        raw = self.db.query_one(sql_stmt, params)
        if raw:
            imgid, user_id, filename, created, md5, email_md5 = raw
            return ImageModel(imgid=imgid, user_id=user_id, filename=filename,
                              created=created, md5=md5, email_md5=email_md5,)
        return None

    def get_image_by_emailmd5(self, email_md5):
        sql_stmt = """
                SELECT imgid, user_id, filename, created, md5, email_md5
                FROM yagra_image
                where email_md5 = %s
                """
        params = (email_md5, )
        raw = self.db.query_one(sql_stmt, params)
        if raw:
            imgid, user_id, filename, created, md5, email_md5 = raw
            return ImageModel(imgid=imgid, user_id=user_id, filename=filename,
                              created=created, md5=md5, email_md5=email_md5,)
        return None

    def get_own_image_count(self, user_id):
        sql_stmt = """SELECT COUNT(*) FROM yagra_image
                WHERE user_id = %s"""
        params = (user_id, )
        raw = self.db.query_one(sql_stmt, params)
        return 0 if raw is None else raw[0]

    def get_own_images(self, user_id, offset=0, limit=10):
        sql_stmt = """
                SELECT imgid, user_id, filename, created, email_md5, md5
                FROM yagra_image WHERE user_id=%s and imgid >=
                    (SELECT imgid FROM yagra_image
                    WHERE user_id=%s ORDER BY imgid LIMIT %s, 1)
                LIMIT %s
                """
        params = (user_id, user_id, offset, limit)
        raw = self.db.query(sql_stmt, params)
        images = []
        if raw:
            for row in raw:
                imgid, user_id, filename, created, md5, email_md5 = row
                images.append(
                    ImageModel(
                        imgid=imgid,
                        user_id=user_id,
                        filename=filename,
                        created=created,
                        md5=md5,
                        email_md5=email_md5,
                    ))
        return images

    def get_user_last_upload_image(self, user_id):
        sql_stmt = """
                SELECT imgid, user_id, filename, created, email_md5, md5
                FROM yagra_image
                WHERE user_id=%s ORDER BY created DESC LIMIT 1
                """
        params = (user_id, )
        raw = self.db.query_one(sql_stmt, params)
        if raw:
            imgid, user_id, filename, created, md5, email_md5 = raw
            return ImageModel(imgid=imgid, user_id=user_id, filename=filename,
                              created=created, md5=md5, email_md5=email_md5,)
        return None
