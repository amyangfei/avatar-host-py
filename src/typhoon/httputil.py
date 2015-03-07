#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import copy
import Cookie
from urlparse import parse_qs

from typhoon.util import native_str


class HTTPConnection(object):
    def __init__(self, stream):
        self.stream = stream

    def write(self, chunk):
        self.stream.write(chunk)

    def close(self):
        if self.stream is not None:
            self.stream.close()


class HTTPRequest(object):
    def __init__(self, method=None, uri=None, version="HTTP/1.1", headers=None,
                 body=None, host=None, files=None, connection=None,
                 ):
        self.method = method
        self.uri = uri
        self.version = version
        self.headers = headers
        self.body = body or b""

        self.host = host or self.headers.get("Host") or "127.0.0.1"
        self.files = files or {}
        self.connection = connection
        self._start_time = time.time()
        self._finish_time = None

        self.path, sep, self.query = uri.partition('?')
        self.arguments = parse_qs(self.query, keep_blank_values=True)
        self.query_arguments = copy.deepcopy(self.arguments)
        self.body_arguments = {}

    def write(self, chunk):
        self.connection.write(chunk)

    @property
    def cookies(self):
        """A dictionary of Cookie.Morsel objects."""
        if not hasattr(self, "_cookies"):
            self._cookies = Cookie.SimpleCookie()
            if "Cookie" in self.headers:
                try:
                    self._cookies.load(native_str(self.headers["Cookie"]))
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
        # norm_name = _normalized_headers[name]
        return self._as_list.get(name, [])

    def get_all(self):
        """Returns an iterable of all (name, value) pairs.

        If a header has multiple values, multiple pairs will be
        returned with the same name.
        """
        for name, values in self._as_list.items():
            for value in values:
                yield (name, value)
