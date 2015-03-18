#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import struct
import StringIO
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


def paginator(current_page, item_counts, item_per_page):
    page_count = (item_counts + item_per_page - 1) / item_per_page

    previous_page = current_page - 1 if current_page > 1 else 1
    has_previous = True if current_page > 1 else False

    next_page = current_page + 1 if current_page < page_count else page_count
    has_next = True if current_page < page_count else False

    show_first = True if previous_page > 1 else False
    show_last = True if next_page < page_count else False

    return {
        "current_page": current_page,
        "previous_page": previous_page,
        "has_previous": has_previous,
        "next_page": next_page,
        "has_next": has_next,
        "page_count": page_count,
        "show_first": show_first,
        "show_last": show_last,
    }


"""get_image_ext is derived from following:
http://stackoverflow.com/questions/7460218/get-image-size-wihout-downloading-it-in-python
https://code.google.com/p/bfg-pages/source/browse/trunk/pages/getimageinfo.py
"""
def get_image_ext(data):
    data = str(data)
    size = len(data)
    ext = ''

    # handle GIFs
    if (size >= 6) and data[:6] in ('GIF87a', 'GIF89a'):
        # Check to see if content_type is correct
        ext = 'gif'

    # See PNG 2. Edition spec (http://www.w3.org/TR/PNG/)
    elif (size >= 8) and data.startswith('\211PNG\r\n\032\n'):
        ext = 'png'

    # handle JPEGs, should starts with 0xff 0xd8 or '\377\330' in octonary
    elif (size >= 2) and data.startswith('\377\330'):
        ext = 'jpeg'

    return ext
