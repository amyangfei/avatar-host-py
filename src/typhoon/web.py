#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import sys
import time
import base64
import httplib
import numbers
import datetime
import traceback
import urlparse
import Cookie
from functools import wraps

import typhoon
from typhoon.log import default_log_setting, app_log
from typhoon.util import (import_object, format_timestamp, unicode_type,
                        json_encode, utf8, unquote_or_none, create_signature)
from typhoon.cgiutil import CGIConnection, CGIRequest, HTTPHeaders


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
            self._reason = utf8(reason)
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

    @property
    def cookies(self):
        return self.request.cookies

    def get_cookie(self, name, default=None):
        """Gets the value of the cookie with the given name, else default."""
        if self.request.cookies is not None and name in self.request.cookies:
            return self.request.cookies[name].value
        return default

    def set_cookie(self, name, value, domain=None, expires=None, path="/",
                   expires_days=None, **kwargs):
        name = utf8(name)
        value = utf8(value)
        if re.search(r"[\x00-\x20]", name + value):
            # Don't let us accidentally inject bad stuff
            raise ValueError("Invalid cookie %r: %r" % (name, value))
        if not hasattr(self, "_new_cookie"):
            self._new_cookie = Cookie.SimpleCookie()
        if name in self._new_cookie:
            del self._new_cookie[name]
        self._new_cookie[name] = value

        """morsel: https://docs.python.org/2/library/cookie.html#morsel-objects
        if morsel is not set, there will be some troubles, such as the default
        path for cookie is the current path.
        """
        morsel = self._new_cookie[name]
        if domain:
            morsel["domain"] = domain
        if expires_days is not None and not expires:
            expires = datetime.datetime.utcnow() + datetime.timedelta(
                days=expires_days)
        if expires:
            morsel["expires"] = format_timestamp(expires)
        if path:
            morsel["path"] = path
        for k, v in kwargs.items():
            if k == 'max_age':
                k = 'max-age'
            if k in ['httponly', 'secure'] and not v:
                continue

            morsel[k] = v

    def clear_cookie(self, name, path="/", domain=None):
        expires = datetime.datetime.utcnow() - datetime.timedelta(days=366)
        self.set_cookie(name, value="", path=path, expires=expires,
                        domain=domain)

    def clear_all_cookies(self, path="/", domain=None):
        for name in self.request.cookies:
            self.clear_cookie(name, path=path, domain=domain)

    def set_secure_cookie(self, name, value, **params):
        expires_days = \
            self.application.settings.get("session_timeout", 86400 * 15) / 86400
        encrypted_cookie = self.encrypt_cookie(name, value)
        self.set_cookie(
                name, encrypted_cookie, expires_days=expires_days, **params)

    def get_secure_cookie(self, name):
        encrypt_data = self.get_cookie(name)
        return self.decrypt_cookie(name, encrypt_data)

    def encrypt_cookie(self, name, value):
        timestamp = utf8(str(int(time.time())))
        value = base64.b64encode(utf8(value))
        secure_key = self.application.settings.get("secure_key")
        signature = create_signature(secure_key, name, value, timestamp)
        value = b"|".join([value, timestamp, signature])
        return value

    def decrypt_cookie(self, name, encrypted_data):
        if not encrypted_data:
            return None
        parts = utf8(encrypted_data).split(b"|")
        if len(parts) != 3:
            return None
        secure_key = self.application.settings.get("secure_key")
        signature = create_signature(secure_key, name, parts[0], parts[1])
        if signature != parts[2]:
            app_log.warn("Invalid cookie signature %r", encrypted_data)
            return None
        session_timeout = self.application.settings.get("session_timeout")
        try:
            timestamp = int(parts[1])
        except ValueError:
            timestamp = 0
        if timestamp < time.time() - session_timeout:
            app_log.warn("Expired cookie %r", encrypted_data)
            return None
        try:
            return base64.b64decode(parts[0])
        except Exception:
            return None

    @property
    def current_user(self):
        if not hasattr(self, "_current_user"):
            self._current_user = self.get_current_user()
        return self._current_user

    @current_user.setter
    def current_user(self, value):
        self._current_user = value

    def get_current_user(self):
        """Override to determine the current user from, e.g., a cookie."""
        return None

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

    def redirect(self, url, permanent=False, status=None):
        if status is None:
            status = 301 if permanent else 302
        else:
            assert isinstance(status, int) and 300 <= status <= 399
        self.set_status(status)
        self.set_header("Location", urlparse.urljoin(utf8(self.request.uri),
                                                     utf8(url)))

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
            self.request._finish_time = time.time()
            app_log.info('%s %s %s %s %.0f ms', self._status_code,
                    self.request.method, self.request.uri, self.request.remote_addr,
                    (self.request._finish_time - self.request._start_time) * 1000)


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
        # At this point get true start time for request processing
        start_time = time.time()
        self.handlers = []
        self.settings = settings
        self.log_setting(**settings)
        self.add_handlers(handlers)
        self.prepare_run_context(StdStream(), start_time)

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

    def prepare_run_context(self, stream, start_time):
        connection = CGIConnection(stream)
        env = os.environ
        headers = {
            "Cookie": env.get("HTTP_COOKIE"),
        }
        request = CGIRequest(
            method = env.get("REQUEST_METHOD"),
            uri = env.get("REQUEST_URI"),
            version = env.get('SERVER_PROTOCOL'),
            headers = headers,
            host = env.get("HTTP_HOST"),
            remote_addr = env.get('REMOTE_ADDR'),
            connection = connection,
            start_time = start_time,
        )
        self._request = request

    def run(self):
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


def authenticated(method):
    """Decorate methods with this to require that the user be logged in."""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            if self.request.method in ("GET", "HEAD"):
                url = self.get_login_url()
                self.redirect(url)
                return
            raise HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper
