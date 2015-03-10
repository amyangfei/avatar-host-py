#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" A micro template engine for python2.
upports expression, template inheritance and extensible macros.

inspired by [moody-templates](https://github.com/etianen/moody-templates)
"""

import re
import os
from functools import partial, wraps


# Template Related Class #######################################################

class TemplateBlock(object):
    def __init__(self, segments, name):
        self.segments = segments
        self._name = name

    def render_value_in_context(self, context):
        # segment is a partial object that can render token_contents with context
        for lineno, segment in self.segments:
            try:
                segment(context)
            except TemplateRenderError:
                raise
            except Exception as e:
                raise TemplateRenderError(str(e), self._name, lineno)


class Template(TemplateBlock):
    def __init__(self, segments, name, params, meta):
        super(Template, self).__init__(segments, name)
        self._params = params
        self._meta = meta

    def render(self, **params):
        context_params = self._params.copy()
        context_params.update(params)
        context = Context(context_params, self._meta, [])
        self.render_value_in_context(context)
        return context.render()

    def render_in_sub_context(self, context, meta):
        """Renders the template in sub context."""
        sub_params = self._params.copy()
        sub_params.update(context.params)
        sub_meta = self._meta.copy()
        sub_meta.update(meta)
        self.render_value_in_context(context.sub_context(sub_params, sub_meta))


class TemplateError(Exception):
    def __init__(self, message, template_name, template_lineno):
        super(TemplateError, self).__init__(message)
        self.tempate_name = template_name
        self.template_lineno = template_lineno

    def __str__(self):
        message = super(TemplateError, self).__str__()
        return "{} [{} on line {}]".\
                format(message, self.template_name, self.template_lineno)


class TemplateRenderError(TemplateError):
    # FIXME: <unprintable TemplateRenderError object>
    pass


class TemplateCompileError(TemplateError):
    # FIXME: <unprintable TemplateCompileError object>
    pass


# Template Parser ##############################################################

RE_TOKEN = re.compile(
    # comment, no token mapping
    r"{#.+?#}"

    # variable, mapping to TOKEN_VAR
    "|{{\s*(.*?)\s*}}"

    # macro, mapping to TOKEN_BLOCK
    "|{%\s*(.*?)\s*%}"

    , re.DOTALL
)

TOKEN_STR = 0
TOKEN_VAR = 1
TOKEN_BLOCK = 2
TOKEN_MAP = {
    TOKEN_STR: "string",
    TOKEN_VAR: "variable",
    TOKEN_BLOCK: "block",
}

class Lexer(object):
    def __init__(self, template_string):
        self.template_string = template_string
        self.lineno = 1
        self.index = 0

    def tokenize(self):
        """Return a list of tokens from a given template_string."""
        for bit in RE_TOKEN.finditer(self.template_string):
            if bit.start() > self.index:
                cur_token = self.template_string[self.index:bit.start()]
                yield self.lineno, TOKEN_MAP[TOKEN_STR], cur_token
                self.lineno += cur_token.count("\n")

            # non-string tokens
            cur_token, token_type = None, -1
            var_token, block_token = bit.groups()
            if var_token:
                cur_token, token_type = var_token, TOKEN_VAR
            elif block_token:
                cur_token, token_type = block_token, TOKEN_BLOCK
            if cur_token is not None:
                yield self.lineno, TOKEN_MAP[token_type], cur_token
                self.lineno += cur_token.count("\n")

            self.index = bit.end()

        if self.index < len(self.template_string):
            yield self.lineno, TOKEN_MAP[TOKEN_STR],\
                self.template_string[self.index:]


def escape_html(value):
    import cgi
    return cgi.escape(value, quote=True)


DEFAULT_ESCAPE_FUNCS = {
    ".html": escape_html,
    ".htm": escape_html,
}


class Parser(object):
    def __init__(self, macros, escape_func=DEFAULT_ESCAPE_FUNCS):
        self._macros = macros
        self._escape_func = escape_func
        self.run = {}

    def compile(self, template_str, name="__string__", params=None, meta=None):
        _, ext = os.path.splitext(name)
        default_meta = {
            "__name__": name,
            "__escape__": self._escape_func.get(ext, None)
        }
        default_meta.update(meta or {})
        params = params or {}
        self.run['tokens'] = Lexer(template_str).tokenize()
        self.run['name'] = name
        segments = self.parse_all_segments(template_str, name)
        return Template(segments, name, params, default_meta)

    def parse_template_segment(self, end_segment_handler):
        segments = []
        for lineno, token_type, token_contents in self.run['tokens']:
            # print lineno, token_type, token_contents
            try:
                if token_type == TOKEN_MAP[TOKEN_STR]:
                    segment = partial(_string_segment, token_contents)
                elif token_type == TOKEN_MAP[TOKEN_VAR]:
                    segment = partial(_var_segment,
                            _val_evaluate(token_contents))
                elif token_type == TOKEN_MAP[TOKEN_BLOCK]:
                    segment = None
                    for macro in self._macros:
                        segment = macro(self, token_contents)
                        if segment:
                            break
                    if not segment:
                        return end_segment_handler(token_contents, segments)
                else:
                    assert False, "{} isn't a valid token type.".\
                            format(token_type)
                segments.append((lineno, segment))
            except TemplateCompileError:
                raise
            except Exception as e:
                raise TemplateCompileError(str(e), self.run.get('name'), lineno)

        # No unknown macro
        return end_segment_handler(None, segments)

    def parse_all_segments(self, template_string, name):
        def end_segment_handler(token_contents, segments):
            if token_contents:
                raise SyntaxError("{{% {} %}} is not a recognized tag." \
                        .format(token_contents))
            return segments
        return self.parse_template_segment(end_segment_handler)

    def parse_block(self, start_tag, end_tag, regex):
        """Parse a block looking for a macro token that matches the given regex
        """
        def end_segment_handler(token_contents, segments):
            if not token_contents:
                raise SyntaxError("{} tag could not find a corresponding {}."\
                        .format(start_tag, end_tag))
            match = regex.match(token_contents)
            if not match:
                raise SyntaxError("{} is not a recognizd tag".\
                        format(token_contents))
            return match, TemplateBlock(segments, self.run.get('name'))
        return self.parse_template_segment(end_segment_handler)


# Context Related ##############################################################

class Context:
    def __init__(self, params, meta, buffer):
        self.params = params
        self.meta = meta
        self.buffer = buffer

    def debug_dump(self):
        return 'params: {}, buffer: {}'.format(self.params, self.buffer)

    def render(self):
        return "".join(self.buffer)

    def sub_context(self, params=None, meta=None):
        sub_params = self.params.copy()
        sub_params.update(params or {})
        sub_meta = self.meta.copy()
        sub_meta.update(meta or {})
        return Context(sub_params, sub_meta, self.buffer)


def _val_evaluate(expression):
    expression = compile(expression, "<string>", "eval")
    """use eval to get the result of the evaluated expression, for example
    >>> eval('name.upper()',{'name':'cpython'}))
    CPYTHON
    """
    def evaluator(context):
        return eval(expression, context.meta, context.params)
    return evaluator


def _string_segment(value, context):
    context.buffer.append(value)


def _var_segment(evaluate, context):
    value = str(evaluate(context))
    escape = context.meta.get("__escape__")
    if escape:
        value = escape(value)
    context.buffer.append(value)


def name_setter(name):
    """Return a function that will render variable in a context
    Thr returned function is like set_name(context, value)
    """
    # like case: for k, v in dictobj.iteritems():
    if "," in name:
        names = [x.strip() for x in name.split(",")]
        def setter(context, value):
            value = iter(value)
            for single_name in names:
                try:
                    context.params[single_name] = next(value)
                except StopIteration:
                    raise ValueError("not enough values to unpack")
            try:
                next(value)
            except StopIteration:
                pass
            else:
                raise ValueError(
                        "need more than {} values to unpack".format(len(names)))
    else:
        names = [name, ]
        def setter(context, value):
            context.params[name] = value
    return setter



# Macro Extension ##############################################################

"""
Each "token_macro" function returns a partial object with the structure of
function(context), also known as "segment" in our system.

Each "token_block" function is the final rendering function.
"""

def token_regex_check(regex):
    regex = re.compile(regex, re.DOTALL)
    def decorator(func):
        @wraps(func)
        def wrapper(parser_run, token):
            match = regex.match(token)
            if match:
                return func(parser_run, *match.groups(), **match.groupdict())
            return None
        return wrapper
    return decorator


def if_block(clauses, else_block, context):
    for evaluate, block in clauses:
        if evaluate(context):
            block.render_value_in_context(context)
            return
    if else_block:
        else_block.render_value_in_context(context)


RE_IF_BLOCK = re.compile("^(elif) (.+?)$|^(else)$|^(endif)$")

@token_regex_check("^if\s+(.+?)$")
def if_macro(parser, expression):
    clauses = []
    else_tag = False
    else_block = None
    while True:
        match, block = parser.parse_block("if", "endif", RE_IF_BLOCK)
        if else_tag:
            else_block = block
        else:
            clauses.append((_val_evaluate(expression), block))
        elif_flag, elif_expression, else_flag, endif_flag = match.groups()
        if elif_flag:
            if else_tag:
                raise SyntaxError("elif tag cannot come after else.")
            expression = elif_expression
        elif else_flag:
            if else_tag:
                raise SyntaxError("Only one else tag is allowed per if")
            else_tag = True
        elif endif_flag:
            break
    return partial(if_block, clauses, else_block)


def for_block(set_name, evaluate, block, context):
    items = evaluate(context)
    for item in items:
        set_name(context, item)
        block.render_value_in_context(context)


RE_ENDFOR = re.compile("^endfor$")

@token_regex_check("^for\s+(.+?)\s+in\s+(.+?)$")
def for_macro(parser, name, variable):
    macth, block = parser.parse_block("for", "endfor", RE_ENDFOR)
    return partial(for_block, name_setter(name), _val_evaluate(variable), block)


def get_template(context, template):
    if isinstance(template, Template):
        return template
    if isinstance(template, str):
        loader = context.meta.get("__loader__")
        if not loader:
            raise ValueError("Cannot load {} by name.".format(template))
        return loader.load(template)
    raise TypeError("Expected a Template or a str, can not be {}."\
            .format(type(template)))


def include_block(evaluate, context):
    template = get_template(context, evaluate(context))
    template.render_in_sub_context(context, {})


@token_regex_check("^include\s+(.+?)$")
def include_macro(parser, expression):
    return partial(include_block, _val_evaluate(expression))


DEFAULT_MACROS = (if_macro, for_macro, include_macro, )


# Template Loader ##############################################################

class BaseSource(object):
    def load(self, template_name):
        raise NotImplementedError


class MemorySource(BaseSource):
    def __init__(self, template_map):
        """template_map mapping from a template name to template content"""
        self.templates = template_map

    def load(self, template_name):
        return self.templates.get(template_name, None)

    def __str__(self):
        return "__memory__"


class DirectorySource(BaseSource):
    def __init__(self, dirname):
        self.dirname = dirname

    def load(self, template_name):
        file_path = os.path.abspath(os.path.join(self.dirname, template_name))
        if os.path.exists(file_path):
            with open(file_path, "r") as template_file:
                return template_file.read()
        return None

    def __str__(self):
        return self.dirname


class TemplateNotFoundError(Exception):
    pass


class Loader(object):
    def __init__(self, sources, parser):
        self._sources = sources
        self._parser = parser
        self._cache = {}

    def clear_cache(self):
        self._cache.clear()

    def compile(self, template_str, name="__string__", params=None, meta=None):
        default_meta = {
            "__loader__": self,
        }
        default_meta.update(meta or {})
        return self._parser.compile(template_str, name, params, default_meta)

    def load(self, template_name):
        """Return the template object if template_name is found in any source,
        else return None.
        """
        if template_name in self._cache:
            return self._cache[template_name]
        for source in self._sources:
            template_contents = source.load(template_name)
            if template_contents is not None:
                compiled_template = self.compile(
                        template_contents, template_name, {}, {})
                self._cache[template_name] = compiled_template
                return compiled_template
        raise TemplateNotFoundError(
                "could not found template {}".format(template_name))

    def render(self, template_name, **params):
        return self.load(template_name).render(**params)


# Public Interface #############################################################

default_parser = Parser(DEFAULT_MACROS)

compiler = default_parser.compile

def render(template, **kwargs):
    return compiler(template).render(**kwargs)
