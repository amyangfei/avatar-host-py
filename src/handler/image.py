#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import hashlib

from typhoon.log import app_log
from typhoon.web import authenticated
from base import BaseHandler, prepare_session
from common.utils import random_image_name
from model.image import ImageDAO


def get_image_fullpath(basepath, filename):
    """future work, extensible image storage"""
    return os.path.join(basepath, filename)


class UploadHandler(BaseHandler):

    @prepare_session
    def get(self, **template_vars):
        if self.current_user is None:
            return self.redirect("/user/login?next=" + self.request.uri)
        return self.render("image/upload.html", **template_vars)

    @authenticated
    @prepare_session
    def post(self, **template_vars):
        user = self.current_user
        upload_file = self.request.upload_files.get("upload")

        _, ext = os.path.splitext(upload_file.filename)
        image_name = random_image_name(user.username) + ext
        image_fullpath = get_image_fullpath(
                self.application.settings.get("upload_path"), image_name)

        # if user has upload this image before, we don't keep more copy.
        md5_checksum = hashlib.md5(upload_file.file.read()).hexdigest()
        image_dao = ImageDAO(self.get_db_config())
        image = image_dao.get_image_by_uid_and_md5(user.uid, md5_checksum)
        if image:
            return self.get(notify=["您已经上传过此图片"])

        with open(image_fullpath, "wb") as img_writer:
            upload_file.file.seek(0)
            img_writer.write(upload_file.file.read())

        email_md5 = "" if user.avatar else hashlib.md5(user.email).hexdigest()
        update_avatar = False if user.avatar else True
        create_result, lastrowid = image_dao.create_image(user_id=user.uid,
                filename=image_name, md5_checksum=md5_checksum,
                email_md5=email_md5, update_avatar=update_avatar)

        if create_result == 1:
            notify="上传图片成功"
            if update_avatar:
                notify += "，并且设置为默认头像"
            return self.get(notify=[notify, ])
        else:
            return self.get(errors=["上传图片失败"])


class AccessHandler(BaseHandler):
    def get(self, email_md5, **template_vars):
        app_log.debug("email_md5: %s", email_md5)
        pass


class ManageHandler(BaseHandler):
    @prepare_session
    def get(self, **template_vars):
        if self.current_user is None:
            return self.redirect("/user/login?next=" + self.request.uri)
        user = self.current_user
        image_dao = ImageDAO(self.get_db_config())
        # TODO: pagination
        own_images = image_dao.get_own_images(user.uid, 0, 3)
        template_vars.update({"images": own_images})
        return self.render("image/manage.html", **template_vars)


