#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Executable module to test unittest-xml-reporting.
"""

import os
from cStringIO import StringIO
import testsuite_cases as testcases
import unittest
import xmlrunner


class XMLTestRunnerTestCase(unittest.TestCase):
    """XMLTestRunner test case.
    """
    
    # Directory where the fixtures are placed
    TEST_FIXTURES_DIR = 'src/xmlrunner/tests/fixtures'
    
    def _fixture(name):
        "Read the content of a XML fixture."
        fixture_file = file('%s/%s.xml' % \
            (XMLTestRunnerTestCase.TEST_FIXTURES_DIR, name))
        content = ''.join(fixture_file.readlines())
        content = content.replace('{{PATH}}', os.path.abspath('.'))
        fixture_file.close()
        return content
    
    _fixture = staticmethod(_fixture)
    
    def _run_test_class(self, test_class, expected=None):
        "Run a test class and compare it to a given fixture."
        expected_xml = ''
        if expected:
            expected_xml = XMLTestRunnerTestCase._fixture(expected)
        self.runner.run(unittest.makeSuite(test_class))
        self.assertEqual(expected_xml, self.stream.getvalue())
    
    def setUp(self):
        "Setup the objects needed to run the tests."
        self.stream = StringIO()
        self.fake_stream = StringIO()
        self.runner = xmlrunner.XMLTestRunner(output=self.stream, \
            stream=self.fake_stream, elapsed_times=False)
    
    def tearDown(self):
        "Free resources after each test."
        self.stream.close()
        self.fake_stream.close()
    
    def test_empty_test_class(self):
        "Empty test class should not generate a XML file."
        self._run_test_class(testcases.EmptyTestCase)
    
    def test_success_test_method(self):
        "Check the XML output of a test class with a successful test method."
        self._run_test_class(testcases.SuccessfulTestCase, \
            'successful_test_case')
    
    def test_failed_test_case(self):
        "Check the XML output of a test class with a failed test method."
        self._run_test_class(testcases.FailedTestCase, \
            'failed_test_case')
    
    def test_errord_test_case(self):
        "Check the XML output of a test class with an errord test method."
        self._run_test_class(testcases.ErrordTestCase, \
            'errord_test_case')
    
    def test_mixed_test_case(self):
        "Check the XML output of a test class with all sorts of outcomes."
        self._run_test_class(testcases.MixedTestCase, \
            'mixed_test_case')


if __name__ == '__main__':
    unittest.main()
