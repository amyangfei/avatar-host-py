#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging

app_log = logging.getLogger('typhoon.application')


def default_log_setting(redirect_path=None, log_level='DEBUG',
                        log_format_str=None):
    """if redirect_path is not specific the program will run silently"""
    if not redirect_path:
        app_log.propagate = False
        handler = logging.StreamHandler(sys.stderr)
        app_log.addHandler(handler)
    else:
        app_log.propagate = False
        app_log.setLevel(log_level)
        log_handler = logging.FileHandler(redirect_path)
        lformat = logging.Formatter(log_format_str) if log_format_str else \
            logging.Formatter('%(asctime)s [%(levelname)s] %(pathname)s'
                              ':%(lineno)s %(message)s')
        log_handler.setFormatter(lformat)
        app_log.addHandler(log_handler)
