#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from typhoon import template

class TestRender(unittest.TestCase):

    def testStringTag(self):
        self.assertEqual(template.render(
            "hello\tworld\n中文"), "hello\tworld\n中文")

    def testCommantTag(self):
        self.assertEqual(template.render("text{# this is a comment #}"), "text")
        self.assertEqual(template.render("{# multi\nline\ncomment #}"), "")

    def testExpressionTag(self):
        self.assertEqual(template.render("{{'hello'}}"), "hello")
        self.assertEqual(template.render("{{('hello '\n'world')}}"), "hello world")
        self.assertEqual(template.render("{{ hello }}", hello="world"), "world")

    def testIfMacro(self):
        # Test single if.
        template1 = template.compiler("{% if test == 'foo' %}foo{% endif %}")
        self.assertEqual(template1.render(test="foo"), "foo")
        self.assertEqual(template1.render(test="bar"), "")
        # Test if and else.
        template2 = template.compiler("{% if test == 'foo' %}foo{% else %}bar{% endif %}")
        self.assertEqual(template2.render(test="foo"), "foo")
        self.assertEqual(template2.render(test="bar"), "bar")
        # Test if, elif and else.
        template3 = template.compiler(
                "{% if test == 'foo' %}foo{% elif test == 'bar' %}bar"
                "{% else %}foobar{% endif %}")
        self.assertEqual(template3.render(test="foo"), "foo")
        self.assertEqual(template3.render(test="bar"), "bar")
        self.assertEqual(template3.render(test=""), "foobar")
        # Test if and elif
        template4 = template.compiler(
                "{% if test == 'foo' %}foo{% elif test == 'bar' %}bar"
                "{% elif test == 'foobar' %}foobar{% endif %}")
        self.assertEqual(template4.render(test="foo"), "foo")
        self.assertEqual(template4.render(test="bar"), "bar")
        self.assertEqual(template4.render(test="foobar"), "foobar")
        self.assertEqual(template4.render(test="no"), "")
        # Test various syntax errors.
        self.assertRaises(template.TemplateCompileError,
                lambda: template.compiler("{% if True %}"))
        self.assertRaises(template.TemplateCompileError,
                lambda: template.compiler(
                    "{% if True %}{% else %}{% elif True %}{% endif %}"))
        self.assertRaises(template.TemplateCompileError,
                lambda: template.compiler(
                    "{% if True %}{% else %}{% else %}{% endif %}"))

    def testForMacro(self):
        # Test basic functionality.
        template1 = template.compiler(
                "{% for i in range(5) %}{{ i }}{% endfor %}")
        self.assertEqual(template1.render(), "01234")
        # Test various syntax errors.
        self.assertRaises(template.TemplateCompileError,
                lambda: template.compiler("{% for n in range(0, 3) %}"))
        # Test variable expansion.
        template2 = template.compiler(
                "{% for n, m in value %}{{ n }}{{ m }}{% endfor %}")
        self.assertEqual(template2.render(value=[["foo", "bar"]]), "foobar")
        self.assertRaises(template.TemplateRenderError,
                lambda: template2.render(value=[["foo"]]))
        self.assertRaises(template.TemplateRenderError,
                lambda: template2.render(value=[["foo", "bar", "foobar"]]))
        template3 = template.compiler(
                "{% for n in range(2) %}"
                "<img src=\"http://img.mxiaonao.me/{{n}}.jpg\" />{% endfor %}")
        self.assertEqual(template3.render(),
                "<img src=\"http://img.mxiaonao.me/0.jpg\" />"
                "<img src=\"http://img.mxiaonao.me/1.jpg\" />")
        template4 = template.compiler(
                "{% for n in range(5) %}{% if n > 2 %}{{ n }}{% endif %}{% endfor %}")
        self.assertEqual(template4.render(), "34")

    def testIncludeMacro(self):
        template1 = template.compiler("template1")
        template2 = template.compiler("template2 include {% include t1 %}")
        self.assertEqual(
                template2.render(t1=template1), "template2 include template1")


test_loader = template.Loader(
    sources = [
        template.MemorySource({
            "base.html": "<html><head>{{ head }}</head><body>{{ body }}</body></html>",
            "include1.html": "<div>{{ content}}</div>",
            "include2.html": "<div>hello</div>",
            "include3.html": "<body>{% include 'include1.html' %}</body>",
            "include4.html": "<body>{% include 'include2.html' %}</body>",
        }),
    ],
    parser = template.default_parser,
)


class TestLoader(unittest.TestCase):

    def setUp(self):
        test_loader.clear_cache()

    def testLoad(self):
        self.assertTrue(test_loader.load("base.html"))

    def testValEval(self):
        self.assertEqual(test_loader.render(
            "base.html", head="hello", body="world"),
            "<html><head>hello</head><body>world</body></html>")

    def testInclude(self):
        self.assertEqual(test_loader.render("include3.html", content="world"),
                "<body><div>world</div></body>")
        self.assertEqual(test_loader.render("include4.html"),
                "<body><div>hello</div></body>")


if __name__ == '__main__':
    unittest.main()
