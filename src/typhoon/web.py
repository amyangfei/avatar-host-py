#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import sys
import time
import httplib
import numbers
import datetime
import traceback

import typhoon
from typhoon.log import default_log_setting, app_log
from typhoon.util import (import_object, format_timestamp, unicode_type,
                        json_encode, utf8, unquote_or_none, native_str)
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

    def set_status(self, status_code, reason=None):
        self._status_code = status_code
        if reason is not None:
            self._reason = native_str(reason)
        else:
            try:
                self._reason = httplib.responses[status_code]
            except KeyError:
                raise ValueError("unknown status code %d", status_code)

    def set_header(self, name, value):
        self._headers[name] = self._convert_header_value(value)

    def _convert_header_value(self, value):
        if isinstance(value, bytes):
            return value
        elif isinstance(value, unicode_type):
            return value.encode('utf-8')
        elif isinstance(value, numbers.Integral):
            return str(value)
        elif isinstance(value, datetime.datetime):
            return format_timestamp(value)
        else:
            raise TypeError("Unsupported header value %r" % value)

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

    def prepare(self):
        pass

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

    def _handle_requeset_exception(self, e):
        if isinstance(e, HTTPError):
            if e.status_code not in httplib.responses and not e.reason:
                # TODO: log error("Bad HTTP status code: %d", e.status_code)
                self.send_error(500, exc_info=sys.exc_info())
            else:
                self.send_error(e.status_code, exc_info=sys.exc_info())
        else:
            self.send_error(500, exc_info=sys.exc_info())

    def write_error(self, status_code, **kwargs):
        # TODO: debug mode switch
        self.set_header('Content-Type', 'text/plain')
        for line in traceback.format_exception(*kwargs["exc_info"]):
            self.write(line)

    def send_error(self, status_code=500, **kwargs):
        """Sends the given HTTP error code to the browser."""
        self.clear()
        reason = kwargs.get('reason')
        if 'exc_info' in kwargs:
            exception = kwargs['exc_info'][1]
            if isinstance(exception, HTTPError) and exception.reason:
                reason = exception.reason
        self.set_status(status_code, reason=reason)
        try:
            self.write_error(status_code, **kwargs)
        except Exception:
            # TODO: log exception
            pass

    def _execute(self, *args):
        try:
            self.prepare()
            getattr(self, self.request.method.lower())(*args)
        except Exception, e:
            self._handle_requeset_exception(e)
        finally:
            self.flush()
            app_log.info('%s %s %s %s', self._status_code, self.request.method,
                        self.request.uri, self.request.remote_addr)


class ErrorHandler(RequestHandler):
    """Generates an error response with ``status_code`` for all requests."""
    def initialize(self, status_code):
        self.set_status(status_code)

    def prepare(self):
        raise HTTPError(self._status_code)

    def check_xsrf_cookie(self):
        pass


class Application(object):
    def __init__(self, handlers=None, **settings):
        self.handlers = []
        self.settings = settings
        self.log_setting(**settings)
        self.add_handlers(handlers)

    def log_setting(self, **settings):
        if 'app_log' in settings:
            app_log_cfg = settings['app_log']
            assert isinstance(app_log_cfg, dict)
            assert 'redirect_path' in app_log_cfg
            redirect_path = app_log_cfg.get('redirect_path')
            log_level = app_log_cfg.get('log_level', 'DEBUG')
            log_format_str = app_log_cfg.get('log_format_str', None)
            default_log_setting(redirect_path, log_level, log_format_str)
        else:
            default_log_setting()

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
        request = HTTPRequest(
            method = env.get("REQUEST_METHOD"),
            uri = env.get("REQUEST_URI"),
            version = env.get('SERVER_PROTOCOL'),
            headers = {},
            host = env.get("HTTP_HOST"),
            cookie_string = env.get('HTTP_COOKIE'),
            remote_addr = env.get('REMOTE_ADDR'),
            connection = connection,
        )
        self._request = request

    def _run(self):
        path_args = []
        handler = None

        for spec in self.handlers:
            match = spec.regex.match(self._request.path)
            if match:
                handler = spec.handler_class(self, self._request)
                path_args = [unquote_or_none(s) for s in match.groups()]
                # TODO: path_kwargs
                break
        if not handler:
            handler = ErrorHandler(self, self._request, status_code=404)

        # TODO: named url pattern using path_kwargs
        handler._execute(*path_args)

    def run(self):
        self._prepare_run(StdStream())
        self._run()
