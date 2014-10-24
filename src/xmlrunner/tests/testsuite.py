#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Executable module to test unittest-xml-reporting.
"""
import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

import xmlrunner
from six import StringIO
from tempfile import mkdtemp
from shutil import rmtree
from glob import glob
import os.path

class XMLTestRunnerTestCase(unittest.TestCase):
    """
    XMLTestRunner test case.
    """
    class DummyTest(unittest.TestCase):
        @unittest.skip("demonstrating skipping")
        def test_skip(self):
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

    def test_basic_unittest_constructs(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        suite.addTest(self.DummyTest('test_skip'))
        suite.addTest(self.DummyTest('test_fail'))
        suite.addTest(self.DummyTest('test_expected_failure'))
        suite.addTest(self.DummyTest('test_unexpected_success'))
        suite.addTest(self.DummyTest('test_error'))
        self._test_xmlrunner(suite)

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

    def test_junitxml_properties(self):
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        suite.properties = dict(key='value')
        self._test_xmlrunner(suite)

    def test_xmlrunner_stream(self):
        stream = self.stream
        output = StringIO()
        runner = xmlrunner.XMLTestRunner(
            stream=stream, output=output, verbosity=self.verbosity,
            **self.runner_kwargs)
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        runner.run(suite)

