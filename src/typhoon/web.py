#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import sys
import time
import urllib
import httplib

import typhoon
from typhoon.util import (import_object, native_str, format_timestamp,
                            unicode_type, json_encode, utf8, debug_log)
from typhoon.httputil import HTTPConnection, HTTPRequest, HTTPHeaders


class StdStream(object):
    def write(self, chunk):
        sys.stdout.write(chunk)


class URLSpec(object):
    """Specifies mappings between URLs and handlers."""
    def __init__(self, pattern, handler):
        if not pattern.endswith('$'):
            pattern += '$'
        self.regex = re.compile(pattern)

        if isinstance(handler, str):
            # import the Module and instantiate the class
            # Must be a fully qualified name (module.ClassName)
            handler = import_object(handler)

        self.handler_class = handler


class HTTPError(Exception):
    """An exception that will turn into an HTTP error response."""

    def __init__(self, status_code, log_message=None, *args, **kwargs):
        self.status_code = status_code
        self.log_message = log_message
        self.args = args
        self.reason = kwargs.get('reason', None)

    def __str__(self):
        message = "HTTP %d: %s" % (
            self.status_code,
            self.reason or httplib.responses.get(self.status_code, 'Unknown'))
        if self.log_message:
            return message + " (" + (self.log_message % self.args) + ")"
        else:
            return message


class RequestHandler(object):
    def __init__(self, application, request, **kwargs):
        super(RequestHandler, self).__init__()

        self.application = application
        self.request = request

        self.clear()
        self.initialize(**kwargs)

    def clear(self):
        """Resets all headers and content for this response."""
        self._headers = HTTPHeaders({
            "Server": "Typhoon CGI Server/%s" % typhoon.version,
            "Content-Type": "text/html; charset=UTF-8",
            "Date": format_timestamp(time.time()),
        })
        self._write_buffer = []
        self._status_code = 200

    def initialize(self):
        """Hook for subclass initialization."""
        pass

    def get(self, *args, **kwargs):
        raise HTTPError(405)

    def post(self, *args, **kwargs):
        raise HTTPError(405)

    def write(self, chunk):
        if not isinstance(chunk, (bytes, unicode_type, dict)):
            raise TypeError(
                "write() only accepts bytes, unicode, and dict objects")
        if isinstance(chunk, dict):
            chunk = json_encode(chunk)
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        chunk = utf8(chunk)
        self._write_buffer.append(chunk)

    def _gen_resp_header(self):
        header_lines = ['Status: {0} {1}'.format(self._status_code,
                httplib.responses.get(self._status_code, 'METHOD NOT FOUND'))]
        for k, v in self._headers.iteritems():
            header_lines.append('{0}: {1}'.format(k, v))
        if hasattr(self, "_new_cookie"):
            for cookie in self._new_cookie.values():
                header_lines.append(
                        'Set-Cookie: {}'.format(cookie.OutputString(None)))
        return '\r\n'.join(header_lines) + '\r\n\r\n'

    def flush(self):
        self.request.write(self._gen_resp_header())
        self.request.write("".join(self._write_buffer))

    def _execute(self, *args):
        # TODO: error handling
        getattr(self, self.request.method.lower())(*args)
        self.flush()


class Application(object):
    def __init__(self, handlers=None, **settings):
        self.handlers = []
        self.settings = settings
        self.add_handlers(handlers)

    def add_handlers(self, handlers):
        """Appends the given handlers to our handler list.

        Host patterns are processed sequentially in the order they were
        added. All matching patterns will be considered.
        """
        for spec in handlers:
            if isinstance(spec, tuple):
                assert len(spec) == 2
            self.handlers.append(URLSpec(*spec))

    def _prepare_run(self, stream):
        connection = HTTPConnection(stream)

        env = os.environ
        debug_log(str(env))

        headers = {}

        request = HTTPRequest(
            method = unicode(env["REQUEST_METHOD"], encoding="utf-8"),
            uri = unicode(env["REQUEST_URI"], encoding="utf-8"),
            version="HTTP/1.1",
            headers=headers,
            host=unicode(env.get("HTTP_HOST"), encoding="utf-8"),
            connection=connection)
        self._request = request

    def _find_handler(self):
        request = self._request
        path = request.path

        for spec in self.handlers:
            match = spec.regex.match(path)
            if match:
                self.handler_class = spec.handler_class(self, request)
                self.handler_args = [
                        unicode(urllib.unquote_plus(native_str(m)), "utf-8")
                        for m in match.groups()]
                return
        # TODO: invalid handler handling

    def _run(self):
        self._find_handler()
        self.handler_class._execute(*self.handler_args)

    def run(self):
        self._prepare_run(StdStream())
        self._run()
