#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Executable module to test unittest-xml-reporting.
"""
import contextlib
import io
import sys

from xmlrunner.unittest import unittest
import xmlrunner
from xmlrunner.result import _DuplicateWriter
from xmlrunner.result import _XMLTestResult
import doctest
import tests.doctest_example
from six import StringIO, BytesIO
from tempfile import mkdtemp
from tempfile import mkstemp
from shutil import rmtree
from glob import glob
from xml.dom import minidom
from lxml import etree
import os
import os.path


def _load_schema():
    path = os.path.join(os.path.dirname(__file__),
                        'vendor/jenkins/xunit-plugin',
                        'junit-10.xsd')
    with open(path, 'r') as schema_file:
        schema_doc = etree.parse(schema_file)
        schema = etree.XMLSchema(schema_doc)
        return schema
    raise RuntimeError('Could not load JUnit schema')  # pragma: no cover


JUnitSchema = _load_schema()


def validate_junit_report(text):
    document = etree.parse(BytesIO(text))
    JUnitSchema.assertValid(document)


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
        self.assertIn('classname="tests.doctest_example.Multiplicator" '
                      'name="threetimes"'.encode('utf8'), output)
        self.assertIn('classname="tests.doctest_example" '
                      'name="twice"'.encode('utf8'), output)


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

        def test_non_ascii_error(self):
            self.assertEqual(u"éçà", 42)

        def test_unsafe_unicode(self):
            print(u"A\x00B\x08C\x0BD\x0C")

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

    def _test_xmlrunner(self, suite, runner=None):
        outdir = self.outdir
        stream = self.stream
        verbosity = self.verbosity
        runner_kwargs = self.runner_kwargs
        if runner is None:
            runner = xmlrunner.XMLTestRunner(
                stream=stream, output=outdir, verbosity=verbosity,
                **runner_kwargs)
        self.assertEqual(0, len(glob(os.path.join(outdir, '*xml'))))
        runner.run(suite)
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
        self.assertIn('classname="tests.testsuite.DummyTest" '
                      'name="test_pass"'.encode('utf8'),
                      output)
        self.assertIn('classname="tests.testsuite.DummySubTest" '
                      'name="test_subTest_pass"'.encode('utf8'),
                      output)

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
            u'<skipped message="demonstrating non-ascii skipping: éçà" '
            u'type="skip"/>'.encode('utf8'),
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
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest(
            'test_non_ascii_runner_buffer_output_fail'))
        outdir = BytesIO()
        runner = xmlrunner.XMLTestRunner(
            stream=self.stream, output=outdir, verbosity=self.verbosity,
            **self.runner_kwargs)

        # allow output non-ascii letters to stdout
        orig_stdout = sys.stdout
        if getattr(sys.stdout, 'buffer', None):
            # Python3
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        else:
            # Python2
            import codecs
            sys.stdout = codecs.getwriter("utf-8")(sys.stdout)

        try:
            runner.run(suite)
        finally:
            if getattr(sys.stdout, 'buffer', None):
                # Python3
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
        self.assertIn(
            b'<testcase classname="tests.testsuite.DummySubTest" '
            b'name="test_subTest_fail (i=0)"',
            output)
        self.assertIn(
            b'<testcase classname="tests.testsuite.DummySubTest" '
            b'name="test_subTest_fail (i=1)"',
            output)

    @unittest.skipIf(not hasattr(unittest.TestCase, 'subTest'),
                     'unittest.TestCase.subTest not present.')
    def test_unittest_subTest_pass(self):
        # Test for issue #85
        suite = unittest.TestSuite()
        suite.addTest(self.DummySubTest('test_subTest_pass'))
        self._test_xmlrunner(suite)

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
        validate_junit_report(output)

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
        validate_junit_report(output)

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
