#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import cgi
import time
import Cookie
from urlparse import parse_qs

from typhoon.util import utf8


class CGIConnection(object):

    def __init__(self, stream):
        self.stream = stream

    def write(self, chunk):
        self.stream.write(chunk)

    def close(self):
        if self.stream is not None:
            self.stream.close()


class CGIRequest(object):

    def __init__(self, method=None, uri=None, version=None, headers=None,
                 body=None, host=None, remote_addr=None, connection=None,
                 start_time=None
                 ):
        self.method = method
        self.uri = uri
        self.version = version
        self.headers = headers

        self.host = host or self.headers.get("Host") or "127.0.0.1"
        self.remote_addr = remote_addr
        self.connection = connection
        self._start_time = start_time or time.time()
        self._finish_time = None

        self.path, sep, self.query = uri.partition('?')
        self.arguments = parse_qs(self.query, keep_blank_values=True)
        self.upload_files = {}

        form = cgi.FieldStorage()
        """FIXME: post request contentType can't be application/json,
        maybe a drawback of python cgi library? Some references:
        https://groups.google.com/forum/#!topic/google-appengine-python/D_Gdp0Svtyg
        http://stackoverflow.com/questions/17247347/why-do-post-file-uploads-in-gae-not-have-access-to-the-cgi-fieldstorage-methods

        post with application/json as content type has bug as following:
            if form.keys():
            raise TypeError, "not indexable"
        """
        for k in form.keys():
            if form[k].file:
                self.upload_files[k] = form[k]
            # here we also set form.getlist(k) to arguments, eg.
            # form['_xsrf'=.file is True
            self.arguments.setdefault(k, []).extend(form.getlist(k))

    def write(self, chunk):
        self.connection.write(chunk)

    @property
    def cookies(self):
        """A dictionary of Cookie.Morsel objects."""
        if not hasattr(self, "_cookies"):
            self._cookies = Cookie.SimpleCookie()
            if "Cookie" in self.headers:
                try:
                    self._cookies.load(utf8(self.headers["Cookie"]))
                except Exception:
                    self._cookies = {}
        return self._cookies


class HTTPHeaders(dict):

    def __init__(self, *args, **kwargs):
        # Don't pass args or kwargs to dict.__init__, as it will bypass
        # our __setitem__
        dict.__init__(self)
        self._as_list = {}
        self._last_key = None
        if (len(args) == 1 and len(kwargs) == 0 and
                isinstance(args[0], HTTPHeaders)):
            # Copy constructor
            for k, v in args[0].get_all():
                self.add(k, v)
        else:
            # Dict-style initialization
            self.update(*args, **kwargs)

    def get_list(self, name):
        """Returns all values for the given header as a list."""
        return self._as_list.get(name, [])

    def get_all(self):
        """Returns an iterable of all (name, value) pairs.

        If a header has multiple values, multiple pairs will be
        returned with the same name.
        """
        for name, values in self._as_list.items():
            for value in values:
                yield (name, value)
