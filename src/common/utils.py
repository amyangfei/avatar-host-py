#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from hashlib import sha1, md5
from random import choice
from string import digits, ascii_lowercase


def generate_salt(length):
    return ''.join(choice(ascii_lowercase + digits) for _ in range(length))


def password_hash(raw_password, salt):
    return sha1(raw_password + ':' + salt).hexdigest()[:32]


def random_image_name(username):
    basestr = "{}_{:.6f}".format(username, time.time())
    return md5(basestr.encode('utf-8')).hexdigest()
