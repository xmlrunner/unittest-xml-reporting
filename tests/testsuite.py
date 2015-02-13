#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Executable module to test unittest-xml-reporting.
"""
import sys

from xmlrunner.unittest import unittest
import xmlrunner
from six import StringIO, BytesIO
from tempfile import mkdtemp
from shutil import rmtree
from glob import glob
from xml.dom import minidom
import os.path


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
                **self.runner_kwargs)
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
            u'<skipped message="demonstrating non-ascii skipping: éçà" type="skip"/>'.encode('utf8'),
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
        suite.addTest( unittest.TestLoader().loadTestsFromTestCase(DummyTestA) );
        suite.addTest( unittest.TestLoader().loadTestsFromTestCase(DummyTestB) );
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
        except Exception as e:
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
        self.assertIn(u"<![CDATA[ABCD\n]]>".encode('utf8'), output)

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
        self._test_xmlrunner(suite)
        testsuite_output = self.stream.getvalue()
        self.assertIn('should be printed', testsuite_output)

    def test_xmlrunner_pass(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        self._test_xmlrunner(suite)

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

    def test_xmlrunner_elapsed_times(self):
        self.runner_kwargs['elapsed_times'] = False
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
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

