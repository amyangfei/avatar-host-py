#!/usr/bin/env python
# -*- coding: utf-8 -*-


import time
import email.utils
import datetime
import numbers
import calendar
import json
import urllib


def import_object(name):
    """Imports an object by name.
    import_object('x') is equivalent to 'import x'.
    import_object('x.y.z') is equivalent to 'from x.y import z'.
    """
    if name.count('.') == 0:
        return __import__(name, None, None)

    parts = name.split('.')
    obj = __import__('.'.join(parts[:-1]), None, None, [parts[-1]], 0)
    try:
        return getattr(obj, parts[-1])
    except AttributeError:
        raise ImportError("No module named %s" % parts[-1])


# python2.x support only
unicode_type = unicode
basestring_type = basestring

_UTF8_TYPES = (bytes, type(None))
def utf8(value):
    """Converts a string argument to a byte string.

    If the argument is already a byte string or None, it is returned unchanged.
    Otherwise it must be a unicode string and is encoded as utf8.
    """
    if isinstance(value, _UTF8_TYPES):
        return value
    if not isinstance(value, unicode_type):
        raise TypeError(
            "Expected bytes, unicode, or None; got %r" % type(value)
        )
    return value.encode("utf-8")


# python 2.x support only
native_str = utf8


def format_timestamp(ts):
    """Formats a timestamp in the format used by HTTP.

    The argument may be a numeric timestamp as returned by `time.time`,
    a time tuple as returned by `time.gmtime`, or a `datetime.datetime`
    object.
    """
    if isinstance(ts, numbers.Real):
        pass
    elif isinstance(ts, (tuple, time.struct_time)):
        ts = calendar.timegm(ts)
    elif isinstance(ts, datetime.datetime):
        ts = calendar.timegm(ts.utctimetuple())
    else:
        raise TypeError("unknown timestamp type: %r" % ts)
    return email.utils.formatdate(ts, usegmt=True)


def json_encode(value):
    """JSON-encodes the given Python object."""
    # JSON permits but does not require forward slashes to be escaped.
    # This is useful when json data is emitted in a <script> tag
    # in HTML, as it prevents </script> tags from prematurely terminating
    # the javscript.  Some json libraries do this escaping by default,
    # although python's standard library does not, so we do it here.
    # http://stackoverflow.com/questions/1580647/json-why-are-forward-slashes-escaped
    return json.dumps(value).replace("</", "<\\/")


def debug_log(log_str, fname='debug.log'):
    with open(fname, 'a+') as f:
        f.write(log_str)
        f.write('\n')


def url_unescape(value, encoding='utf-8', plus=True):
    """Decodes the given value from a URL.

    The argument may be either a byte or unicode string.

    If encoding is None, the result will be a byte string.  Otherwise,
    the result is a unicode string in the specified encoding.

    If ``plus`` is true (the default), plus signs will be interpreted
    as spaces (literal plus signs must be represented as "%2B").  This
    is appropriate for query strings and form-encoded values but not
    for the path component of a URL.  Note that this default is the
    reverse of Python's urllib module.

    """
    unquote = (urllib.unquote_plus if plus else urllib.unquote)
    if encoding is None:
        return unquote(utf8(value))
    else:
        return unicode_type(unquote(utf8(value)), encoding)

def unquote_or_none(s):
    """None-safe wrapper around url_unescape to handle unamteched optional
    groups correctly.

    Note that args are passed as bytes so the handler can decide what
    encoding to use.
    """
    if s is None:
        return s
    return url_unescape(s, encoding=None, plus=False)
