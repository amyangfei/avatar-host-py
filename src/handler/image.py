#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import hashlib

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

        with open(image_fullpath, "wb") as img_writer:
            img_writer.write(upload_file.file.read())
            # calculate the md5 checksum of image, so move file cursor
            upload_file.file.seek(0)
            md5_checksum = hashlib.md5(upload_file.file.read()).hexdigest()

        create_result = ImageDAO().create_image(user_id=user.uid,
                filename=image_name, md5_checksum=md5_checksum)
        if create_result == 1:
            return self.get(notify=["上传图片成功"])
        else:
            return self.get(errors=["上传图片失败"])
