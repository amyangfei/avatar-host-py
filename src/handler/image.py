#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import hashlib
import mimetypes

from typhoon.log import app_log
from typhoon.web import authenticated
from typhoon.util import format_timestamp
from base import BaseHandler, prepare_session
from common.utils import random_image_name, paginator
from model.image import ImageDAO


def get_image_fullpath(basepath, filename):
    """future work, extensible image storage"""
    return os.path.join(basepath, filename)


def get_upload_image_fullpath(request_handler, filename):
    basepath = request_handler.application.settings.get("upload_path")
    return get_image_fullpath(basepath, filename)


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

        if upload_file.filename == "":
            return self.get(errors=["请指定上传的图片"])

        _, ext = os.path.splitext(upload_file.filename)
        image_name = random_image_name(user.username) + ext
        image_fullpath = get_upload_image_fullpath(self, image_name)

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


class AccessHandlerV1(BaseHandler):
    def get(self, email_md5, **template_vars):
        image_dao = ImageDAO(self.get_db_config())
        image = image_dao.get_image_by_emailmd5(email_md5)
        if image:
            image_fullpath = get_upload_image_fullpath(self, image.filename)
        else:
            image_fullpath = get_image_fullpath("static/img", "default.png")

        try:
            f = open(image_fullpath, "rb")
            img = f.read()
            self.write(img)
            self.set_header("Content-Length", len(img))

            fs = os.stat(image_fullpath)
            etag = "{0}-{1}-{2}".format(fs.st_ino, int(fs.st_mtime), fs.st_size)

            if etag is None:
                return self.set_status(500)
            if self.request.headers.get("If-None-Match") == etag:
                return self.set_status(304)
            else:
                self.set_header("ETag", etag)
                # "Last-Modified" is not the modified time of file, it's the
                # timestamp that certain image is set as avatar.
                self.set_header("Last-Modified", format_timestamp(time.time()))

            _, ext = os.path.splitext(image_fullpath)
            mimetype = mimetypes.types_map.get(ext, "image/jpeg")
            self.set_header("Content-Type", mimetype)
        except IOError, e:
            app_log.error("file %s not found %s", image_fullpath, e)
            self.set_status(500)


class AccessHandlerV2(BaseHandler):
    def get(self, email_md5, **template_vars):
        image_dao = ImageDAO(self.get_db_config())
        image = image_dao.get_image_by_emailmd5(email_md5)
        if image:
            image_url = image.get_url()
        else:
            image_url = "/static/img/default.png"

        self.redirect(image_url)


class ManageHandler(BaseHandler):
    @prepare_session
    def get(self, **template_vars):
        if self.current_user is None:
            return self.redirect("/user/login?next=" + self.request.uri)

        user = self.current_user
        image_dao = ImageDAO(self.get_db_config())

        # simple pagination
        own_images_count = image_dao.get_own_image_count(user.uid)
        limit = 3
        try:
            page_count = (own_images_count + limit - 1) / limit
            page = int(self.get_argument("page", "1"))
            if page_count != 0 and page > page_count:
                page = page_count
        except ValueError:
            page = 1
        offset = (page - 1) * limit
        own_images = image_dao.get_own_images(user.uid, offset, limit)

        paginations = paginator(page, own_images_count, limit)
        template_vars.update(paginations)
        template_vars.update({"images": own_images, "count": own_images_count})
        template_vars.update({"active_page": "manage"})

        return self.render("image/manage.html", **template_vars)


class SetAvatarHandler(BaseHandler):
    @authenticated
    @prepare_session
    def post(self, **template_vars):
        user = self.current_user
        image_id = self.get_argument("image_id")
        image_dao = ImageDAO(self.get_db_config())
        image  = image_dao.get_image_by_id(image_id)

        if image is None:
            self.write({"status": "fail", "msg": "图片不存在"})
            return

        if user.avatar == image.imgid:
            self.write({"status": "ok", "msg": "这就是您当前的头像，无需更换"})
            return

        image_dao.update_user_avatar(user.uid, image.imgid,
                hashlib.md5(user.email).hexdigest())

        new_avatar = image.get_url()
        self.write({"status": "ok", "msg": "更新头像成功",
                    "new_avatar": new_avatar})
