#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Executable module to test unittest-xml-reporting.
"""
from __future__ import print_function

import contextlib
import io
import sys

from xmlrunner.unittest import unittest
import xmlrunner
from xmlrunner.result import _DuplicateWriter
from xmlrunner.result import _XMLTestResult
from xmlrunner.result import resolve_filename
import doctest
import tests.doctest_example
from io import StringIO, BytesIO
from tempfile import mkdtemp
from tempfile import mkstemp
from shutil import rmtree
from glob import glob
from xml.dom import minidom
from lxml import etree
import os
import os.path
from unittest import mock


def _load_schema(version):
    path = os.path.join(
        os.path.dirname(__file__),
        'vendor/jenkins/xunit-plugin', version, 'junit-10.xsd')
    with open(path, 'r') as schema_file:
        schema_doc = etree.parse(schema_file)
        schema = etree.XMLSchema(schema_doc)
        return schema
    raise RuntimeError('Could not load JUnit schema')  # pragma: no cover


def validate_junit_report(version, text):
    document = etree.parse(BytesIO(text))
    schema = _load_schema(version)
    schema.assertValid(document)


class DoctestTest(unittest.TestCase):

    def test_doctest_example(self):
        suite = doctest.DocTestSuite(tests.doctest_example)
        outdir = BytesIO()
        stream = StringIO()
        runner = xmlrunner.XMLTestRunner(
            stream=stream, output=outdir, verbosity=0)
        runner.run(suite)
        outdir.seek(0)
        output = outdir.read()
        self.assertIn('classname="tests.doctest_example.Multiplicator"'.encode('utf8'), output)
        self.assertIn('name="threetimes"'.encode('utf8'), output)
        self.assertIn('classname="tests.doctest_example"'.encode('utf8'), output)
        self.assertIn('name="twice"'.encode('utf8'), output)


@contextlib.contextmanager
def capture_stdout_stderr():
    """
    context manager to capture stdout and stderr
    """
    orig_stdout = sys.stdout
    orig_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    try:
        yield (sys.stdout, sys.stderr)
    finally:
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr


def _strip_xml(xml, changes):
    doc = etree.fromstring(xml)
    for xpath, attributes in changes.items():
        for node in doc.xpath(xpath):
            for attrib in node.attrib.keys():
                if attrib not in attributes:
                    del node.attrib[attrib]
    return etree.tostring(doc)


def some_decorator(f):
    # for issue #195
    code = """\
def wrapper(*args, **kwargs):
    return func(*args, **kwargs)
"""
    evaldict = dict(func=f)
    exec(code, evaldict)
    return evaldict['wrapper']


class XMLTestRunnerTestCase(unittest.TestCase):
    """
    XMLTestRunner test case.
    """
    class DummyTest(unittest.TestCase):

        @unittest.skip("demonstrating skipping")
        def test_skip(self):
            pass   # pragma: no cover

        @unittest.skip(u"demonstrating non-ascii skipping: éçà")
        def test_non_ascii_skip(self):
            pass   # pragma: no cover

        def test_pass(self):
            pass

        def test_fail(self):
            self.assertTrue(False)

        @unittest.expectedFailure
        def test_expected_failure(self):
            self.assertTrue(False)

        @unittest.expectedFailure
        def test_unexpected_success(self):
            pass

        def test_error(self):
            1 / 0

        def test_cdata_section(self):
            print('<![CDATA[content]]>')

        def test_invalid_xml_chars_in_doc(self):
            """
            Testing comments, -- is not allowed, or invalid xml 1.0 chars such as \x0c
            """
            pass

        def test_non_ascii_error(self):
            self.assertEqual(u"éçà", 42)

        def test_unsafe_unicode(self):
            print(u"A\x00B\x08C\x0BD\x0C")

        def test_output_stdout_and_stderr(self):
            print('test on stdout')
            print('test on stderr', file=sys.stderr)

        def test_runner_buffer_output_pass(self):
            print('should not be printed')

        def test_runner_buffer_output_fail(self):
            print('should be printed')
            self.fail('expected to fail')

        def test_output(self):
            print('test message')

        def test_non_ascii_runner_buffer_output_fail(self):
            print(u'Where is the café ?')
            self.fail(u'The café could not be found')

    class DummySubTest(unittest.TestCase):

        def test_subTest_pass(self):
            for i in range(2):
                with self.subTest(i=i):
                    pass

        def test_subTest_fail(self):
            for i in range(2):
                with self.subTest(i=i):
                    self.fail('this is a subtest.')

        def test_subTest_error(self):
            for i in range(2):
                with self.subTest(i=i):
                    raise Exception('this is a subtest')

        def test_subTest_mixed(self):
            for i in range(2):
                with self.subTest(i=i):
                    self.assertLess(i, 1, msg='this is a subtest.')

        def test_subTest_with_dots(self):
            for i in range(2):
                with self.subTest(module='hello.world.subTest{}'.format(i)):
                    self.fail('this is a subtest.')

    class DecoratedUnitTest(unittest.TestCase):

        @some_decorator
        def test_pass(self):
            pass

    class DummyErrorInCallTest(unittest.TestCase):

        def __call__(self, result):
            try:
                raise Exception('Massive fail')
            except Exception:
                result.addError(self, sys.exc_info())
                return

        def test_pass(self):
            # it is expected not to be called.
            pass  # pragma: no cover

    class DummyRefCountTest(unittest.TestCase):
        class dummy(object):
            pass
        def test_fail(self):
            inst = self.dummy()
            self.assertTrue(False)

    def setUp(self):
        self.stream = StringIO()
        self.outdir = mkdtemp()
        self.verbosity = 0
        self.runner_kwargs = {}
        self.addCleanup(rmtree, self.outdir)

    def _test_xmlrunner(self, suite, runner=None, outdir=None):
        if outdir is None:
            outdir = self.outdir
        stream = self.stream
        verbosity = self.verbosity
        runner_kwargs = self.runner_kwargs
        if runner is None:
            runner = xmlrunner.XMLTestRunner(
                stream=stream, output=outdir, verbosity=verbosity,
                **runner_kwargs)
        if isinstance(outdir, BytesIO):
            self.assertFalse(outdir.getvalue())
        else:
            self.assertEqual(0, len(glob(os.path.join(outdir, '*xml'))))
        runner.run(suite)
        if isinstance(outdir, BytesIO):
            self.assertTrue(outdir.getvalue())
        else:
            self.assertEqual(1, len(glob(os.path.join(outdir, '*xml'))))
        return runner

    def test_basic_unittest_constructs(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        suite.addTest(self.DummyTest('test_skip'))
        suite.addTest(self.DummyTest('test_fail'))
        suite.addTest(self.DummyTest('test_expected_failure'))
        suite.addTest(self.DummyTest('test_unexpected_success'))
        suite.addTest(self.DummyTest('test_error'))
        self._test_xmlrunner(suite)

    def test_classnames(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        suite.addTest(self.DummySubTest('test_subTest_pass'))
        outdir = BytesIO()
        stream = StringIO()
        runner = xmlrunner.XMLTestRunner(
            stream=stream, output=outdir, verbosity=0)
        runner.run(suite)
        outdir.seek(0)
        output = outdir.read()
        output = _strip_xml(output, {
            '//testsuite': (),
            '//testcase': ('classname', 'name'),
            '//failure': ('message',),
        })
        self.assertRegexpMatches(
            output,
            r'classname="tests\.testsuite\.(XMLTestRunnerTestCase\.)?'
            r'DummyTest" name="test_pass"'.encode('utf8'),
        )
        self.assertRegexpMatches(
            output,
            r'classname="tests\.testsuite\.(XMLTestRunnerTestCase\.)?'
            r'DummySubTest" name="test_subTest_pass"'.encode('utf8'),
        )

    def test_expected_failure(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_expected_failure'))
        outdir = BytesIO()

        self._test_xmlrunner(suite, outdir=outdir)

        self.assertNotIn(b'<failure', outdir.getvalue())
        self.assertNotIn(b'<error', outdir.getvalue())
        self.assertIn(b'<skip', outdir.getvalue())

    def test_unexpected_success(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_unexpected_success'))
        outdir = BytesIO()

        self._test_xmlrunner(suite, outdir=outdir)

        self.assertNotIn(b'<failure', outdir.getvalue())
        self.assertIn(b'<error', outdir.getvalue())
        self.assertNotIn(b'<skip', outdir.getvalue())

    def test_xmlrunner_non_ascii(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_non_ascii_skip'))
        suite.addTest(self.DummyTest('test_non_ascii_error'))
        outdir = BytesIO()
        runner = xmlrunner.XMLTestRunner(
            stream=self.stream, output=outdir, verbosity=self.verbosity,
            **self.runner_kwargs)
        runner.run(suite)
        outdir.seek(0)
        output = outdir.read()
        self.assertIn(
            u'message="demonstrating non-ascii skipping: éçà"'.encode('utf8'),
            output)

    def test_xmlrunner_safe_xml_encoding_name(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        outdir = BytesIO()
        runner = xmlrunner.XMLTestRunner(
            stream=self.stream, output=outdir, verbosity=self.verbosity,
            **self.runner_kwargs)
        runner.run(suite)
        outdir.seek(0)
        output = outdir.read()
        firstline = output.splitlines()[0]
        # test for issue #74
        self.assertIn('encoding="UTF-8"'.encode('utf8'), firstline)

    def test_xmlrunner_check_for_valid_xml_streamout(self):
        """
        This test checks if the xml document is valid if there are more than
        one testsuite and the output of the report is a single stream.
        """
        class DummyTestA(unittest.TestCase):

            def test_pass(self):
                pass

        class DummyTestB(unittest.TestCase):

            def test_pass(self):
                pass

        suite = unittest.TestSuite()
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(DummyTestA))
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(DummyTestB))
        outdir = BytesIO()
        runner = xmlrunner.XMLTestRunner(
            stream=self.stream, output=outdir, verbosity=self.verbosity,
            **self.runner_kwargs)
        runner.run(suite)
        outdir.seek(0)
        output = outdir.read()
        # Finally check if we have a valid XML document or not.
        try:
            minidom.parseString(output)
        except Exception as e:  # pragma: no cover
            # note: we could remove the try/except, but it's more crude.
            self.fail(e)

    def test_xmlrunner_unsafe_unicode(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_unsafe_unicode'))
        outdir = BytesIO()
        runner = xmlrunner.XMLTestRunner(
            stream=self.stream, output=outdir, verbosity=self.verbosity,
            **self.runner_kwargs)
        runner.run(suite)
        outdir.seek(0)
        output = outdir.read()
        self.assertIn(u"<![CDATA[ABCD\n]]>".encode('utf8'),
                      output)

    def test_xmlrunner_non_ascii_failures(self):
        self._xmlrunner_non_ascii_failures()

    def test_xmlrunner_non_ascii_failures_buffered_output(self):
        self._xmlrunner_non_ascii_failures(buffer=True)

    def _xmlrunner_non_ascii_failures(self, buffer=False):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest(
            'test_non_ascii_runner_buffer_output_fail'))
        outdir = BytesIO()
        runner = xmlrunner.XMLTestRunner(
            stream=self.stream, output=outdir, verbosity=self.verbosity,
            buffer=buffer, **self.runner_kwargs)

        # allow output non-ascii letters to stdout
        orig_stdout = sys.stdout
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

        try:
            runner.run(suite)
        finally:
            # Not to be closed when TextIOWrapper is disposed.
            sys.stdout.detach()
            sys.stdout = orig_stdout
        outdir.seek(0)
        output = outdir.read()
        self.assertIn(
            u'Where is the café ?'.encode('utf8'),
            output)
        self.assertIn(
            u'The café could not be found'.encode('utf8'),
            output)

    @unittest.expectedFailure
    def test_xmlrunner_buffer_output_pass(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_runner_buffer_output_pass'))
        self._test_xmlrunner(suite)
        testsuite_output = self.stream.getvalue()
        # Since we are always buffering stdout/stderr
        # it is currently troublesome to print anything at all
        # and be consistent with --buffer option (issue #59)
        self.assertIn('should not be printed', testsuite_output)
        # this will be fixed when using the composite approach
        # that was under development in the rewrite branch.

    def test_xmlrunner_buffer_output_fail(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_runner_buffer_output_fail'))
        # --buffer option
        self.runner_kwargs['buffer'] = True
        self._test_xmlrunner(suite)
        testsuite_output = self.stream.getvalue()
        self.assertIn('should be printed', testsuite_output)

    def test_xmlrunner_output_without_buffer(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_output'))
        with capture_stdout_stderr() as r:
            self._test_xmlrunner(suite)
        output_from_test = r[0].getvalue()
        self.assertIn('test message', output_from_test)

    def test_xmlrunner_output_with_buffer(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_output'))
        # --buffer option
        self.runner_kwargs['buffer'] = True
        with capture_stdout_stderr() as r:
            self._test_xmlrunner(suite)
        output_from_test = r[0].getvalue()
        self.assertNotIn('test message', output_from_test)

    def test_xmlrunner_stdout_stderr_recovered_without_buffer(self):
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        self._test_xmlrunner(suite)
        self.assertIs(orig_stdout, sys.stdout)
        self.assertIs(orig_stderr, sys.stderr)

    def test_xmlrunner_stdout_stderr_recovered_with_buffer(self):
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        # --buffer option
        self.runner_kwargs['buffer'] = True
        self._test_xmlrunner(suite)
        self.assertIs(orig_stdout, sys.stdout)
        self.assertIs(orig_stderr, sys.stderr)
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))

    @unittest.skipIf(not hasattr(unittest.TestCase, 'subTest'),
                     'unittest.TestCase.subTest not present.')
    def test_unittest_subTest_fail(self):
        # test for issue #77
        outdir = BytesIO()
        runner = xmlrunner.XMLTestRunner(
            stream=self.stream, output=outdir, verbosity=self.verbosity,
            **self.runner_kwargs)
        suite = unittest.TestSuite()
        suite.addTest(self.DummySubTest('test_subTest_fail'))
        runner.run(suite)
        outdir.seek(0)
        output = outdir.read()
        output = _strip_xml(output, {
            '//testsuite': (),
            '//testcase': ('classname', 'name'),
            '//failure': ('message',),
        })
        self.assertRegexpMatches(
            output,
            br'<testcase classname="tests\.testsuite\.'
            br'(XMLTestRunnerTestCase\.)?DummySubTest" '
            br'name="test_subTest_fail \(i=0\)"')
        self.assertRegexpMatches(
            output,
            br'<testcase classname="tests\.testsuite\.'
            br'(XMLTestRunnerTestCase\.)?DummySubTest" '
            br'name="test_subTest_fail \(i=1\)"')

    @unittest.skipIf(not hasattr(unittest.TestCase, 'subTest'),
                     'unittest.TestCase.subTest not present.')
    def test_unittest_subTest_error(self):
        # test for issue #155
        outdir = BytesIO()
        runner = xmlrunner.XMLTestRunner(
            stream=self.stream, output=outdir, verbosity=self.verbosity,
            **self.runner_kwargs)
        suite = unittest.TestSuite()
        suite.addTest(self.DummySubTest('test_subTest_error'))
        runner.run(suite)
        outdir.seek(0)
        output = outdir.read()
        output = _strip_xml(output, {
            '//testsuite': (),
            '//testcase': ('classname', 'name'),
            '//failure': ('message',),
        })
        self.assertRegexpMatches(
            output,
            br'<testcase classname="tests\.testsuite\.'
            br'(XMLTestRunnerTestCase\.)?DummySubTest" '
            br'name="test_subTest_error \(i=0\)"')
        self.assertRegexpMatches(
            output,
            br'<testcase classname="tests\.testsuite\.'
            br'(XMLTestRunnerTestCase\.)?DummySubTest" '
            br'name="test_subTest_error \(i=1\)"')


    @unittest.skipIf(not hasattr(unittest.TestCase, 'subTest'),
                     'unittest.TestCase.subTest not present.')
    def test_unittest_subTest_mixed(self):
        # test for issue #155
        outdir = BytesIO()
        runner = xmlrunner.XMLTestRunner(
            stream=self.stream, output=outdir, verbosity=self.verbosity,
            **self.runner_kwargs)
        suite = unittest.TestSuite()
        suite.addTest(self.DummySubTest('test_subTest_mixed'))
        runner.run(suite)
        outdir.seek(0)
        output = outdir.read()
        output = _strip_xml(output, {
            '//testsuite': (),
            '//testcase': ('classname', 'name'),
            '//failure': ('message',),
        })
        self.assertNotIn(
            'name="test_subTest_mixed (i=0)"'.encode('utf8'),
            output)
        self.assertIn(
            'name="test_subTest_mixed (i=1)"'.encode('utf8'),
            output)

    @unittest.skipIf(not hasattr(unittest.TestCase, 'subTest'),
                     'unittest.TestCase.subTest not present.')
    def test_unittest_subTest_pass(self):
        # Test for issue #85
        suite = unittest.TestSuite()
        suite.addTest(self.DummySubTest('test_subTest_pass'))
        self._test_xmlrunner(suite)

    @unittest.skipIf(not hasattr(unittest.TestCase, 'subTest'),
                     'unittest.TestCase.subTest not present.')
    def test_unittest_subTest_with_dots(self):
        # Test for issue #85
        suite = unittest.TestSuite()
        suite.addTest(self.DummySubTest('test_subTest_with_dots'))
        outdir = BytesIO()

        self._test_xmlrunner(suite, outdir=outdir)

        xmlcontent = outdir.getvalue().decode()

        # Method name
        self.assertNotIn('name="subTest', xmlcontent, 'parsing of test method name is not done correctly')
        self.assertIn('name="test_subTest_with_dots (module=\'hello.world.subTest', xmlcontent)

        # Class name
        matchString = 'classname="tests.testsuite.XMLTestRunnerTestCase.DummySubTest.test_subTest_with_dots (module=\'hello.world"'
        self.assertNotIn(matchString, xmlcontent, 'parsing of class name is not done correctly')
        self.assertIn('classname="tests.testsuite.XMLTestRunnerTestCase.DummySubTest"', xmlcontent)

    def test_xmlrunner_pass(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        self._test_xmlrunner(suite)

    def test_xmlrunner_failfast(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_fail'))
        suite.addTest(self.DummyTest('test_pass'))
        outdir = BytesIO()
        runner = xmlrunner.XMLTestRunner(
            stream=self.stream, output=outdir,
            verbosity=self.verbosity, failfast=True,
            **self.runner_kwargs)
        runner.run(suite)
        outdir.seek(0)
        output = outdir.read()
        self.assertIn('test_fail'.encode('utf8'), output)
        self.assertNotIn('test_pass'.encode('utf8'), output)

    def test_xmlrunner_verbose(self):
        self.verbosity = 1
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        self._test_xmlrunner(suite)

    def test_xmlrunner_showall(self):
        self.verbosity = 2
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        self._test_xmlrunner(suite)

    def test_xmlrunner_cdata_section(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_cdata_section'))
        self._test_xmlrunner(suite)

    def test_xmlrunner_invalid_xml_chars_in_doc(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_invalid_xml_chars_in_doc'))
        outdir = BytesIO()
        runner = xmlrunner.XMLTestRunner(
            stream=self.stream, output=outdir, verbosity=self.verbosity,
            **self.runner_kwargs)
        runner.run(suite)
        outdir.seek(0)
        output = outdir.read()
        # Finally check if we have a valid XML document or not.
        try:
            minidom.parseString(output)
        except Exception as e:  # pragma: no cover
            # note: we could remove the try/except, but it's more crude.
            self.fail(e)

    def test_xmlrunner_outsuffix(self):
        self.runner_kwargs['outsuffix'] = '.somesuffix'
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        self._test_xmlrunner(suite)
        xmlfile = glob(os.path.join(self.outdir, '*xml'))[0]
        assert xmlfile.endswith('.somesuffix.xml')

    def test_xmlrunner_nosuffix(self):
        self.runner_kwargs['outsuffix'] = ''
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        self._test_xmlrunner(suite)
        xmlfile = glob(os.path.join(self.outdir, '*xml'))[0]
        xmlfile = os.path.basename(xmlfile)
        assert xmlfile.endswith('DummyTest.xml')

    def test_junitxml_properties(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        suite.properties = dict(key='value')
        self._test_xmlrunner(suite)

    def test_junitxml_xsd_validation_order(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_fail'))
        suite.addTest(self.DummyTest('test_pass'))
        suite.addTest(self.DummyTest('test_output_stdout_and_stderr'))
        suite.properties = dict(key='value')
        outdir = BytesIO()
        runner = xmlrunner.XMLTestRunner(
            stream=self.stream, output=outdir, verbosity=self.verbosity,
            **self.runner_kwargs)
        runner.run(suite)
        outdir.seek(0)
        output = outdir.read()
        # poor man's schema validation; see issue #90
        i_properties = output.index('<properties>'.encode('utf8'))
        i_system_out = output.index('<system-out>'.encode('utf8'))
        i_system_err = output.index('<system-err>'.encode('utf8'))
        i_testcase = output.index('<testcase'.encode('utf8'))
        self.assertTrue(i_properties < i_testcase <
                        i_system_out < i_system_err)
        # XSD validation - for good measure.
        validate_junit_report('14c6e39c38408b9ed6280361484a13c6f5becca7', output)

    def test_junitxml_xsd_validation_empty_properties(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_fail'))
        suite.addTest(self.DummyTest('test_pass'))
        suite.properties = None
        outdir = BytesIO()
        runner = xmlrunner.XMLTestRunner(
            stream=self.stream, output=outdir, verbosity=self.verbosity,
            **self.runner_kwargs)
        runner.run(suite)
        outdir.seek(0)
        output = outdir.read()
        self.assertNotIn('<properties>'.encode('utf8'), output)
        validate_junit_report('14c6e39c38408b9ed6280361484a13c6f5becca7', output)

    @unittest.skipIf(hasattr(sys, 'pypy_version_info'),
                     'skip - PyPy + lxml seems to be hanging')
    def test_xunit_plugin_transform(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_fail'))
        suite.addTest(self.DummyTest('test_pass'))
        suite.properties = None
        outdir = BytesIO()
        runner = xmlrunner.XMLTestRunner(
            stream=self.stream, output=outdir, verbosity=self.verbosity,
            **self.runner_kwargs)
        runner.run(suite)
        outdir.seek(0)
        output = outdir.read()

        validate_junit_report('14c6e39c38408b9ed6280361484a13c6f5becca7', output)
        with self.assertRaises(etree.DocumentInvalid):
            validate_junit_report('ae25da5089d4f94ac6c4669bf736e4d416cc4665', output)

        from xmlrunner.extra.xunit_plugin import transform
        transformed = transform(output)
        validate_junit_report('14c6e39c38408b9ed6280361484a13c6f5becca7', transformed)
        validate_junit_report('ae25da5089d4f94ac6c4669bf736e4d416cc4665', transformed)
        self.assertIn('test_pass'.encode('utf8'), transformed)
        self.assertIn('test_fail'.encode('utf8'), transformed)

    def test_xmlrunner_elapsed_times(self):
        self.runner_kwargs['elapsed_times'] = False
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        self._test_xmlrunner(suite)

    def test_xmlrunner_resultclass(self):
        class Result(_XMLTestResult):
            pass

        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        self.runner_kwargs['resultclass'] = Result
        self._test_xmlrunner(suite)

    def test_xmlrunner_stream(self):
        stream = self.stream
        output = BytesIO()
        runner = xmlrunner.XMLTestRunner(
            stream=stream, output=output, verbosity=self.verbosity,
            **self.runner_kwargs)
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        runner.run(suite)

    def test_xmlrunner_stream_empty_testsuite(self):
        stream = self.stream
        output = BytesIO()
        runner = xmlrunner.XMLTestRunner(
            stream=stream, output=output, verbosity=self.verbosity,
            **self.runner_kwargs)
        suite = unittest.TestSuite()
        runner.run(suite)

    def test_xmlrunner_output_subdir(self):
        stream = self.stream
        output = os.path.join(self.outdir, 'subdir')
        runner = xmlrunner.XMLTestRunner(
            stream=stream, output=output, verbosity=self.verbosity,
            **self.runner_kwargs)
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        runner.run(suite)

    def test_xmlrunner_patched_stdout(self):
        old_stdout, old_stderr = sys.stdout, sys.stderr
        try:
            sys.stdout, sys.stderr = StringIO(), StringIO()
            suite = unittest.TestSuite()
            suite.addTest(self.DummyTest('test_pass'))
            suite.properties = dict(key='value')
            self._test_xmlrunner(suite)
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

    def test_opaque_decorator(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DecoratedUnitTest('test_pass'))
        self._test_xmlrunner(suite)
        testsuite_output = self.stream.getvalue()
        self.assertNotIn('IOError:', testsuite_output)

    def test_xmlrunner_error_in_call(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyErrorInCallTest('test_pass'))
        self._test_xmlrunner(suite)
        testsuite_output = self.stream.getvalue()
        self.assertIn('Exception: Massive fail', testsuite_output)

    @unittest.skipIf(not hasattr(sys, 'getrefcount'),
                     'skip - PyPy does not have sys.getrefcount.')
    @unittest.skipIf((3, 0) <= sys.version_info < (3, 4),
                     'skip - test not garbage collected. '
                     'https://bugs.python.org/issue11798.')
    def test_xmlrunner_hold_traceback(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyRefCountTest('test_fail'))
        countBeforeTest = sys.getrefcount(self.DummyRefCountTest.dummy)
        runner = self._test_xmlrunner(suite)
        countAfterTest = sys.getrefcount(self.DummyRefCountTest.dummy)
        self.assertEqual(countBeforeTest, countAfterTest)

    class StderrXMLTestRunner(xmlrunner.XMLTestRunner):
        """
        XMLTestRunner that outputs to sys.stderr that might be replaced

        Though XMLTestRunner defaults to use sys.stderr as stream,
        it cannot be replaced e.g. by replaced by capture_stdout_stderr(),
        as it's already resolved.
        This class resolved sys.stderr lazily and outputs to replaced sys.stderr.
        """
        def __init__(self, **kwargs):
            super(XMLTestRunnerTestCase.StderrXMLTestRunner, self).__init__(
                stream=sys.stderr,
                **kwargs
            )

    def test_test_program_succeed_with_buffer(self):
        with capture_stdout_stderr() as r:
            unittest.TestProgram(
                module=self.__class__.__module__,
                testRunner=self.StderrXMLTestRunner,
                argv=[
                    sys.argv[0],
                    '-b',
                    'XMLTestRunnerTestCase.DummyTest.test_runner_buffer_output_pass',
                ],
                exit=False,
            )
        self.assertNotIn('should not be printed', r[0].getvalue())
        self.assertNotIn('should not be printed', r[1].getvalue())

    def test_test_program_succeed_wo_buffer(self):
        with capture_stdout_stderr() as r:
            unittest.TestProgram(
                module=self.__class__.__module__,
                testRunner=self.StderrXMLTestRunner,
                argv=[
                    sys.argv[0],
                    'XMLTestRunnerTestCase.DummyTest.test_runner_buffer_output_pass',
                ],
                exit=False,
            )
        self.assertIn('should not be printed', r[0].getvalue())
        self.assertNotIn('should not be printed', r[1].getvalue())

    def test_test_program_fail_with_buffer(self):
        with capture_stdout_stderr() as r:
            unittest.TestProgram(
                module=self.__class__.__module__,
                testRunner=self.StderrXMLTestRunner,
                argv=[
                    sys.argv[0],
                    '-b',
                    'XMLTestRunnerTestCase.DummyTest.test_runner_buffer_output_fail',
                ],
                exit=False,
            )
        self.assertNotIn('should be printed', r[0].getvalue())
        self.assertIn('should be printed', r[1].getvalue())

    def test_test_program_fail_wo_buffer(self):
        with capture_stdout_stderr() as r:
            unittest.TestProgram(
                module=self.__class__.__module__,
                testRunner=self.StderrXMLTestRunner,
                argv=[
                    sys.argv[0],
                    'XMLTestRunnerTestCase.DummyTest.test_runner_buffer_output_fail',
                ],
                exit=False,
            )
        self.assertIn('should be printed', r[0].getvalue())
        self.assertNotIn('should be printed', r[1].getvalue())

    def test_partialmethod(self):
        from functools import partialmethod
        def test_partialmethod(test):
            pass
        class TestWithPartialmethod(unittest.TestCase):
            pass
        setattr(
            TestWithPartialmethod,
            'test_partialmethod',
            partialmethod(test_partialmethod),
        )
        suite = unittest.TestSuite()
        suite.addTest(TestWithPartialmethod('test_partialmethod'))
        self._test_xmlrunner(suite)



class DuplicateWriterTestCase(unittest.TestCase):
    def setUp(self):
        fd, self.file = mkstemp()
        self.fh = os.fdopen(fd, 'w')
        self.buffer = StringIO()
        self.writer = _DuplicateWriter(self.fh, self.buffer)

    def tearDown(self):
        self.buffer.close()
        self.fh.close()
        os.unlink(self.file)

    def getFirstContent(self):
        with open(self.file, 'r') as f:
            return f.read()

    def getSecondContent(self):
        return self.buffer.getvalue()

    def test_flush(self):
        self.writer.write('foobarbaz')
        self.writer.flush()
        self.assertEqual(self.getFirstContent(), self.getSecondContent())

    def test_writable(self):
        self.assertTrue(self.writer.writable())

    def test_writelines(self):
        self.writer.writelines([
            'foo\n',
            'bar\n',
            'baz\n',
        ])
        self.writer.flush()
        self.assertEqual(self.getFirstContent(), self.getSecondContent())

    def test_write(self):
        # try long buffer (1M)
        buffer = 'x' * (1024 * 1024)
        wrote = self.writer.write(buffer)
        self.writer.flush()
        self.assertEqual(self.getFirstContent(), self.getSecondContent())
        self.assertEqual(wrote, len(self.getSecondContent()))


class XMLProgramTestCase(unittest.TestCase):
    @mock.patch('sys.argv', ['xmlrunner', '-o', 'flaf'])
    @mock.patch('xmlrunner.runner.XMLTestRunner')
    @mock.patch('sys.exit')
    def test_xmlrunner_output(self, exiter, testrunner):
        xmlrunner.runner.XMLTestProgram()

        kwargs = dict(
            buffer=mock.ANY,
            failfast=mock.ANY,
            verbosity=mock.ANY,
            warnings=mock.ANY,
            output='flaf',
        )

        if sys.version_info[:2] > (3, 4):
            kwargs.update(tb_locals=mock.ANY)

        testrunner.assert_called_once_with(**kwargs)
        exiter.assert_called_once_with(False)

    @mock.patch('sys.argv', ['xmlrunner', '--output-file', 'test.xml'])
    @mock.patch('xmlrunner.runner.open')
    @mock.patch('xmlrunner.runner.XMLTestRunner')
    @mock.patch('sys.exit')
    def test_xmlrunner_output_file(self, exiter, testrunner, opener):
        xmlrunner.runner.XMLTestProgram()
        opener.assert_called_once_with('test.xml', 'wb')
        open_file = opener()
        open_file.close.assert_called_with()

        kwargs = dict(
            buffer=mock.ANY,
            failfast=mock.ANY,
            verbosity=mock.ANY,
            warnings=mock.ANY,
            output=open_file,
        )

        if sys.version_info[:2] > (3, 4):
            kwargs.update(tb_locals=mock.ANY)

        testrunner.assert_called_once_with(**kwargs)
        exiter.assert_called_once_with(False)


class ResolveFilenameTestCase(unittest.TestCase):
    @mock.patch('os.path.relpath')
    def test_resolve_filename_relative(self, relpath):
        relpath.return_value = 'somefile.py'
        filename = resolve_filename('/path/to/somefile.py')
        self.assertEqual(filename, 'somefile.py')

    @mock.patch('os.path.relpath')
    def test_resolve_filename_outside(self, relpath):
        relpath.return_value = '../../../tmp/somefile.py'
        filename = resolve_filename('/tmp/somefile.py')
        self.assertEqual(filename, '/tmp/somefile.py')

    @mock.patch('os.path.relpath')
    def test_resolve_filename_error(self, relpath):
        relpath.side_effect = ValueError("ValueError: path is on mount 'C:', start on mount 'D:'")
        filename = resolve_filename('C:\\path\\to\\somefile.py')
        self.assertEqual(filename, 'C:\\path\\to\\somefile.py')
