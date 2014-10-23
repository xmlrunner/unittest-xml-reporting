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

    def test_xmlrunner(self):
        stream = StringIO()
        outdir = mkdtemp()
        self.addCleanup(rmtree, outdir)
        runner = xmlrunner.XMLTestRunner(
            stream=stream, output=outdir, verbosity=0)
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        suite.addTest(self.DummyTest('test_skip'))
        suite.addTest(self.DummyTest('test_fail'))
        suite.addTest(self.DummyTest('test_expected_failure'))
        suite.addTest(self.DummyTest('test_unexpected_success'))
        suite.addTest(self.DummyTest('test_error'))
        self.assertEqual(0, len(glob(os.path.join(outdir, '*xml'))))
        runner.run(suite)
        self.assertEqual(1, len(glob(os.path.join(outdir, '*xml'))))

    def test_xmlrunner_pass(self):
        stream = StringIO()
        outdir = mkdtemp()
        self.addCleanup(rmtree, outdir)
        runner = xmlrunner.XMLTestRunner(
            stream=stream, output=outdir, verbosity=0)
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        self.assertEqual(0, len(glob(os.path.join(outdir, '*xml'))))
        runner.run(suite)
        self.assertEqual(1, len(glob(os.path.join(outdir, '*xml'))))