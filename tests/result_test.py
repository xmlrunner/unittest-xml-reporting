from StringIO import StringIO

import unittest

import xml.etree.ElementTree as ET

import xmlrunner
import sys

# Test suite used to test XMLTestResult
import fixture


_TIME_REGEXP = '^\d+\.\d+$'

# doesn't handle xpath with "[]"
no_predicate_support = unittest.skipIf(sys.version_info < (2,7),
    'xml.etree.ElementPath predicate support missing')


class XMLTestResultTest(unittest.TestCase):
    """XMLTestResult test cases.
    """

    def setUp(self):
        self.stream = StringIO()

        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(fixture)

        runner = xmlrunner.XMLTestRunner(stream=StringIO(), output=self.stream, outsuffix='lombra')
        runner.run(suite)

        self.xml = self.stream.getvalue()
        self.root_node = ET.fromstring(self.xml)

    def test_testsuites_tag(self):
        self.assertEqual(self.root_node.tag, 'testsuites')
        self.assertEqual(self.root_node.attrib['name'], 'TestSuites')
        self.assertRegexpMatches(self.root_node.attrib['time'], _TIME_REGEXP)

    def test_testsuites_test_counter(self):
        tests = self.root_node.findall('.//testcase')
        self.assertEqual(int(self.root_node.attrib['tests']), len(tests))

    def test_testsuites_failure_counter(self):
        failures = self.root_node.findall('.//failure')
        self.assertEqual(int(self.root_node.attrib['failures']), len(failures))

    def test_testsuite_error_counter(self):
        errors = self.root_node.findall('.//error')
        self.assertEqual(int(self.root_node.attrib['errors']), len(errors))

    def test_testsuite_count(self):
        self.assertEqual(len(self.root_node.findall('./testsuite')), 2)

    def test_first_testsuite_tag(self):
        tag = self.root_node.findall('./testsuite')[0]
        self.assertEqual(tag.attrib['name'], 'tests.fixture.TestSequenceFunctions')
        self.assertRegexpMatches(tag.attrib['time'], _TIME_REGEXP)

    @no_predicate_support
    def test_first_testsuite_test_counter(self):
        tag = self.root_node.findall('./testsuite')[0]
        tests = self.root_node.findall('.//testsuite[1]/testcase')
        self.assertEqual(int(tag.attrib['tests']), len(tests))

    @no_predicate_support
    def test_first_testsuite_skipped_counter(self):
        tag = self.root_node.findall('./testsuite')[0]
        skipped = self.root_node.findall('.//testsuite[1]//skipped')
        self.assertEqual(int(tag.attrib['skipped']), len(skipped))

    @no_predicate_support
    def test_first_testsuite_skipped_invalid_utf8_reason(self):
        tag = self.root_node.findall('./testsuite[1]/testcase/skipped')[0]
        self.assertEqual(tag.attrib['message'], u'some reason\ufffd\ufffd')

    @no_predicate_support
    def test_first_testsuite_unexpected_success(self):
        tag = self.root_node.findall('./testsuite[1]/testcase[@name="Expected failure test"]/failure')[0]
        self.assertEqual(tag.attrib['message'], 'Unexpected success')

    @no_predicate_support
    def test_first_testsuite_failure_counter(self):
        tag = self.root_node.findall('./testsuite')[0]
        failures = self.root_node.findall('.//testsuite[1]//failure')
        self.assertEqual(int(tag.attrib['failures']), len(failures))

    @no_predicate_support
    def test_first_testsuite_error_counter(self):
        tag = self.root_node.findall('./testsuite')[0]
        errors = self.root_node.findall('.//testsuite[1]//error')
        self.assertEqual(int(tag.attrib['errors']), len(errors))

    def test_testcase_success_invalid_utf8_stderr(self):
        stderr = self.root_node.findall('./testsuite/testcase/system-err')[0]
        self.assertEqual(stderr.text.strip(), u'this is stderr\ufffd\ufffd')

    @no_predicate_support
    def test_testcase_error_invalid_utf8_msg(self):
        error = self.root_node.findall('./testsuite/testcase[@name="test_error"]/error')[0]
        self.assertEqual(error.attrib['type'], 'RuntimeError')
        self.assertEqual(error.attrib['message'], u'Error msg\ufffd\ufffd')

        self.assertRegexpMatches(error.text, 'Traceback \(most recent call last\):')
        self.assertRegexpMatches(error.text, 'File ".*/tests/fixture\.py",.*, in test_error')

    def test_last_testsuite_tag(self):
        tag = self.root_node.findall('./testsuite')[1]
        self.assertEqual(tag.attrib['name'], 'tests.fixture.TestSomething')
        self.assertRegexpMatches(tag.attrib['time'], _TIME_REGEXP)

    @no_predicate_support
    def test_last_testsuite_test_counter(self):
        tag = self.root_node.findall('./testsuite[last()]')[0]
        tests = self.root_node.findall('.//testsuite[last()]/testcase')
        self.assertEqual(int(tag.attrib['tests']), len(tests))

    @no_predicate_support
    def test_last_testsuite_skipped_counter(self):
        tag = self.root_node.findall('./testsuite[last()]')[0]
        skipped = self.root_node.findall('.//testsuite[last()]//skipped')
        self.assertEqual(int(tag.attrib['skipped']), len(skipped))

    @no_predicate_support
    def test_last_testsuite_failure_counter(self):
        tag = self.root_node.findall('./testsuite[last()]')[0]
        failures = self.root_node.findall('.//testsuite[last()]//failure')
        self.assertEqual(int(tag.attrib['failures']), len(failures))

    @no_predicate_support
    def test_last_testsuite_error_counter(self):
        tag = self.root_node.findall('./testsuite[last()]')[0]
        errors = self.root_node.findall('.//testsuite[last()]//error')
        self.assertEqual(int(tag.attrib['errors']), len(errors))

    @no_predicate_support
    def test_last_testsuite_first_testcase_tag(self):
        tag = self.root_node.findall('./testsuite[last()]/testcase')[0]
        self.assertEqual(tag.attrib['name'], 'test_invalid_xml_unicode')
        self.assertRegexpMatches(tag.attrib['time'], _TIME_REGEXP)

    @no_predicate_support
    def test_last_testsuite_first_testcase_invalid_utf8_stdout(self):
        stdout = self.root_node.findall('./testsuite[last()]/testcase[1]/system-out')[0]
        self.assertEqual(stdout.text.strip(), u'invalid xml: \ufffd\ufffd\xfffe')
