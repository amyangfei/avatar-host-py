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
