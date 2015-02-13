# -*- coding: utf-8

from xmlrunner.unittest import unittest

import xml.etree.ElementTree as ET
from xml.dom.minidom import Document

from xmlrunner import builder
import six


class TestXMLContextTest(unittest.TestCase):
    """TestXMLContext test cases.
    """

    def setUp(self):
        self.doc = Document()
        self.root = builder.TestXMLContext(self.doc)

    def test_current_element_tag_name(self):
        self.root.begin('tag', 'context-name')
        self.assertEqual(self.root.element_tag(), 'tag')

    def test_current_context_name(self):
        self.root.begin('tag', 'context-name')
        name = self.root.element.getAttribute('name')
        self.assertEqual(name, 'context-name')

    def test_current_context_invalid_unicode_name(self):
        self.root.begin('tag', six.u('context-name\x01\x0B'))
        name = self.root.element.getAttribute('name')
        self.assertEqual(name, six.u('context-name\uFFFD\uFFFD'))

    def test_increment_valid_testsuites_counters(self):
        self.root.begin('testsuites', 'name')

        for c in ('tests', 'failures', 'errors', 'skipped'):
            self.root.increment_counter(c)

        element = self.root.end()

        with self.assertRaises(KeyError):
            element.attributes['skipped']

        for c in ('tests', 'failures', 'errors'):
            value = element.attributes[c].value
            self.assertEqual(value, '1')

    def test_increment_valid_testsuite_counters(self):
        self.root.begin('testsuite', 'name')

        for c in ('tests', 'failures', 'errors', 'skipped'):
            self.root.increment_counter(c)

        element = self.root.end()

        for c in ('tests', 'failures', 'errors', 'skipped'):
            value = element.attributes[c].value
            self.assertEqual(value, '1')

    def test_increment_counters_for_unknown_context(self):
        self.root.begin('unknown', 'name')

        for c in ('tests', 'failures', 'errors', 'skipped', 'invalid'):
            self.root.increment_counter(c)

        element = self.root.end()

        for c in ('tests', 'failures', 'errors', 'skipped', 'invalid'):
            with self.assertRaises(KeyError):
                element.attributes[c]

    def test_empty_counters_on_end_context(self):
        self.root.begin('testsuite', 'name')
        element = self.root.end()

        for c in ('tests', 'failures', 'errors', 'skipped'):
            self.assertEqual(element.attributes[c].value, '0')

    def test_add_time_attribute_on_end_context(self):
        self.root.begin('testsuite', 'name')
        element = self.root.end()

        element.attributes['time'].value


class TestXMLBuilderTest(unittest.TestCase):
    """TestXMLBuilder test cases.
    """

    def setUp(self):
        self.builder = builder.TestXMLBuilder()
        self.doc = self.builder._xml_doc
        self.builder.begin_context('testsuites', 'name')

        self.valid_chars = six.u('выбор')

        self.invalid_chars = '\x01'
        self.invalid_chars_replace = six.u('\ufffd')

    def test_root_has_no_parent(self):
        self.assertIsNone(self.builder.current_context().parent)

    def test_current_context_tag(self):
        self.assertEqual(self.builder.context_tag(), 'testsuites')

    def test_begin_nested_context(self):
        root = self.builder.current_context()

        self.builder.begin_context('testsuite', 'name')

        self.assertEqual(self.builder.context_tag(), 'testsuite')
        self.assertIs(self.builder.current_context().parent, root)

    def test_end_inexistent_context(self):
        self.builder = builder.TestXMLBuilder()

        self.assertFalse(self.builder.end_context())
        self.assertEqual(len(self.doc.childNodes), 0)

    def test_end_root_context(self):
        root = self.builder.current_context()

        self.assertTrue(self.builder.end_context())
        self.assertIsNone(self.builder.current_context())

        # No contexts left
        self.assertFalse(self.builder.end_context())

        doc_children = self.doc.childNodes

        self.assertEqual(len(doc_children), 1)
        self.assertEqual(len(doc_children[0].childNodes), 0)
        self.assertEqual(doc_children[0].tagName, root.element_tag())

    def test_end_nested_context(self):
        self.builder.begin_context('testsuite', 'name')
        nested = self.builder.current_context()

        self.assertTrue(self.builder.end_context())

        # Only updates the document when all contexts end
        self.assertEqual(len(self.doc.childNodes), 0)

    def test_end_all_context_stack(self):
        root = self.builder.current_context()

        self.builder.begin_context('testsuite', 'name')
        nested = self.builder.current_context()

        self.assertTrue(self.builder.end_context())
        self.assertTrue(self.builder.end_context())

        # No contexts left
        self.assertFalse(self.builder.end_context())

        root_child = self.doc.childNodes

        self.assertEqual(len(root_child), 1)
        self.assertEqual(root_child[0].tagName, root.element_tag())

        nested_child = root_child[0].childNodes

        self.assertEqual(len(nested_child), 1)
        self.assertEqual(nested_child[0].tagName, nested.element_tag())

    def test_append_valid_unicode_cdata_section(self):
        self.builder.append_cdata_section('tag', self.valid_chars)
        self.builder.end_context()

        root_child = self.doc.childNodes[0]

        cdata_container = root_child.childNodes[0]
        self.assertEqual(cdata_container.tagName, 'tag')

        cdata = cdata_container.childNodes[0]
        self.assertEqual(cdata.data, self.valid_chars)

    def test_append_invalid_unicode_cdata_section(self):
        self.builder.append_cdata_section('tag', self.invalid_chars)
        self.builder.end_context()

        root_child = self.doc.childNodes[0]
        cdata_container = root_child.childNodes[0]

        cdata = cdata_container.childNodes[0]
        self.assertEqual(cdata.data, self.invalid_chars_replace)

    def test_append_cdata_closing_tags_into_cdata_section(self):
        self.builder.append_cdata_section('tag',']]>')
        self.builder.end_context()
        root_child = self.doc.childNodes[0]
        cdata_container = root_child.childNodes[0]
        self.assertEqual(len(cdata_container.childNodes), 2)
        self.assertEqual(cdata_container.childNodes[0].data, ']]')
        self.assertEqual(cdata_container.childNodes[1].data, '>')

    def test_append_tag_with_valid_unicode_values(self):
        self.builder.append('tag', self.valid_chars, attr=self.valid_chars)
        self.builder.end_context()

        root_child = self.doc.childNodes[0]
        tag = root_child.childNodes[0]

        self.assertEqual(tag.tagName, 'tag')
        self.assertEqual(tag.getAttribute('attr'), self.valid_chars)
        self.assertEqual(tag.childNodes[0].data, self.valid_chars)

    def test_append_tag_with_invalid_unicode_values(self):
        self.builder.append('tag', self.invalid_chars, attr=self.invalid_chars)
        self.builder.end_context()

        root_child = self.doc.childNodes[0]
        tag = root_child.childNodes[0]

        self.assertEqual(tag.tagName, 'tag')
        self.assertEqual(tag.getAttribute('attr'), self.invalid_chars_replace)
        self.assertEqual(tag.childNodes[0].data, self.invalid_chars_replace)

    def test_increment_root_context_counter(self):
        self.builder.increment_counter('tests')
        self.builder.end_context()

        root_child = self.doc.childNodes[0]

        self.assertEqual(root_child.tagName, 'testsuites')
        self.assertEqual(root_child.getAttribute('tests'), '1')

    def test_increment_nested_context_counter(self):
        self.builder.increment_counter('tests')

        self.builder.begin_context('testsuite', 'name')
        self.builder.increment_counter('tests')

        self.builder.end_context()
        self.builder.end_context()

        root_child = self.doc.childNodes[0]
        nested_child = root_child.childNodes[0]

        self.assertEqual(root_child.tagName, 'testsuites')
        self.assertEqual(nested_child.getAttribute('tests'), '1')
        self.assertEqual(root_child.getAttribute('tests'), '2')

    def test_finish_nested_context(self):
        self.builder.begin_context('testsuite', 'name')

        tree = ET.fromstring(self.builder.finish())

        self.assertEqual(tree.tag, 'testsuites')
        self.assertEqual(len(tree.findall("./testsuite")), 1)
