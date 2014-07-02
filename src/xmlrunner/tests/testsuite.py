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

class XMLTestRunnerTestCase(unittest.TestCase):
    """
    XMLTestRunner test case.
    """
    class DummyTest(unittest.TestCase):
        @unittest.skip("demonstrating skipping")
        def test_skip(self):
            pass
        def test_pass(self):
            pass
        def test_fail(self):
            self.assertTrue(False)

    def test_xmlrunner(self):
        runner = xmlrunner.XMLTestRunner(verbosity=0)
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_pass'))
        suite.addTest(self.DummyTest('test_skip'))
        suite.addTest(self.DummyTest('test_fail'))
        runner.run(suite)

if __name__ == '__main__':
    unittest.main()
