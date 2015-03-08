#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import sys
import time
import httplib

import typhoon
from typhoon.util import (import_object, format_timestamp, unicode_type,
                        json_encode, utf8, debug_log, unquote_or_none)
from typhoon.httputil import HTTPConnection, HTTPRequest, HTTPHeaders


class StdStream(object):
    def write(self, chunk):
        sys.stdout.write(chunk)


class URLSpec(object):
    """Specifies mappings between URLs and handlers."""
    def __init__(self, pattern, handler, kwargs=None):
        if not pattern.endswith('$'):
            pattern += '$'
        self.regex = re.compile(pattern)

        if isinstance(handler, str):
            # import the Module and instantiate the class
            # Must be a fully qualified name (module.ClassName)
            handler = import_object(handler)

        self.handler_class = handler
        self.handler_kwargs = kwargs or {}


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


class MissingArgumentError(HTTPError):
    """Exception raised by `RequestHandler.get_argument`."""

    def __init__(self, arg_name):
        super(MissingArgumentError, self).__init__(
            400, 'Missing argument %s' % arg_name)
        self.arg_name = arg_name


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

    def get_arguments(self, name):
        args = []
        for v in self.request.arguments.get(name, []):
            args.append(v)
        return args

    _ARG_DEFAULT = []

    def get_argument(self, name, default=_ARG_DEFAULT):
        args = self.get_arguments(name)
        if not args:
            if default is self._ARG_DEFAULT:
                raise MissingArgumentError(name)
            return default
        return args[-1]

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
                assert len(spec) in (2, 3)
            self.handlers.append(URLSpec(*spec))

    def _prepare_run(self, stream):
        connection = HTTPConnection(stream)

        env = os.environ
        debug_log(str(env))

        headers = {}

        request = HTTPRequest(
            method = env.get("REQUEST_METHOD"),
            uri = env.get("REQUEST_URI"),
            version = env.get('SERVER_PROTOCOL'),
            headers = headers,
            host = env.get("HTTP_HOST"),
            cookie = env.get('HTTP_COOKIE'),
            remote_addr = env.get('HTTP_COOKIE'),
            connection = connection,
        )
        self._request = request

    def _find_handler(self):
        request = self._request
        path = request.path

        for spec in self.handlers:
            match = spec.regex.match(path)
            if match:
                self.handler_class = spec.handler_class(self, request)
                self.path_args = [unquote_or_none(s) for s in match.groups()]
                self.handler_kwargs = spec.handler_kwargs
                return
        # TODO: invalid handler handling

    def _run(self):
        self._find_handler()
        self.handler_class._execute(*self.path_args, **self.handler_kwargs)

    def run(self):
        self._prepare_run(StdStream())
        self._run()
