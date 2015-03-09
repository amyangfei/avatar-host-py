#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from typhoon import template

class TestRender(unittest.TestCase):
    def testStringTag(self):
        self.assertEqual(template.render("hello\tworld\n中文"), "hello\tworld\n中文")
    def testCommantTag(self):
        self.assertEqual(template.render("text{# this is a comment #}"), "text")
        self.assertEqual(template.render("{# multi\nline\ncomment #}"), "")
    def testExpressionTag(self):
        self.assertEqual(template.render("{{'hello'}}"), "hello")
        self.assertEqual(template.render("{{('hello '\n'world')}}"), "hello world")
        self.assertEqual(template.render("{{ hello }}", hello="world"), "world")


if __name__ == '__main__':
    unittest.main()
