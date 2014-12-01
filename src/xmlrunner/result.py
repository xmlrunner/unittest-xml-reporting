
import os
import sys
import time
import six
import re

from .unittest import TestResult, _TextTestResult

try:
    # Removed in Python 3
    from StringIO import StringIO
except ImportError:
    from io import StringIO



# Matches invalid XML1.0 unicode characters, like control characters:
# http://www.w3.org/TR/2006/REC-xml-20060816/#charsets
INVALID_XML_1_0_UNICODE_RE = re.compile(
    u'[\x00-\x08\x0B\x0C\x0E-\x1F\uD800-\uDFFF\uFFFE\uFFFF]', re.UNICODE)


def xml_safe_unicode(base, encoding='utf-8'):
    """Return a unicode string containing only valid XML characters.

    encoding - if base is a byte string it is first decoded to unicode
        using this encoding.
    """
    if isinstance(base, six.binary_type):
        base = base.decode(encoding)
    return INVALID_XML_1_0_UNICODE_RE.sub('', base)


def to_unicode(data):
    """Returns unicode in Python2 and str in Python3"""
    if six.PY3:
         return six.text_type(data)
    try:
        # Try utf8
        return six.text_type(data)
    except UnicodeDecodeError as err:
        return repr(data).decode('utf8', 'replace')


def safe_unicode(data, encoding=None):
    return xml_safe_unicode(to_unicode(data), encoding)


def testcase_name(test_method):
    testcase = type(test_method)

    # Ignore module name if it is '__main__'
    module = testcase.__module__ + '.'
    if module == '__main__.':
        module = ''
    result = module + testcase.__name__
    return result


class _TestInfo(object):
    """
    This class keeps useful information about the execution of a
    test method.
    """

    # Possible test outcomes
    (SUCCESS, FAILURE, ERROR, SKIP) = range(4)

    def __init__(self, test_result, test_method, outcome=SUCCESS, err=None):
        self.test_result = test_result
        self.outcome = outcome
        self.elapsed_time = 0
        self.err = err
        self.stdout = test_result._stdout_data
        self.stderr = test_result._stderr_data

        self.test_description = self.test_result.getDescription(test_method)
        self.test_exception_info = (
            '' if outcome in (self.SUCCESS, self.SKIP)
            else self.test_result._exc_info_to_string(
                    self.err, test_method)
        )

        self.test_name = testcase_name(test_method)
        self.test_id = test_method.id()

    def id(self):
        return self.test_id

    def test_finished(self):
        """Save info that can only be calculated once a test has run.
        """
        self.elapsed_time = \
            self.test_result.stop_time - self.test_result.start_time

    def get_description(self):
        """
        Return a text representation of the test method.
        """
        return self.test_description

    def get_error_info(self):
        """
        Return a text representation of an exception thrown by a test
        method.
        """
        return self.test_exception_info


class _XMLTestResult(_TextTestResult):
    """
    A test result class that can express test results in a XML report.

    Used by XMLTestRunner.
    """
    def __init__(self, stream=sys.stderr, descriptions=1, verbosity=1,
                 elapsed_times=True, properties=None):
        _TextTestResult.__init__(self, stream, descriptions, verbosity)
        self.buffer = True  # we are capturing test output
        self._stdout_data = None
        self._stderr_data = None
        self.successes = []
        self.callback = None
        self.elapsed_times = elapsed_times
        self.properties = None # junit testsuite properties

    def _prepare_callback(self, test_info, target_list, verbose_str,
                          short_str):
        """
        Appends a _TestInfo to the given target list and sets a callback
        method to be called by stopTest method.
        """
        target_list.append(test_info)

        def callback():
            """Prints the test method outcome to the stream, as well as
            the elapsed time.
            """

            test_info.test_finished()

            # Ignore the elapsed times for a more reliable unit testing
            if not self.elapsed_times:
                self.start_time = self.stop_time = 0

            if self.showAll:
                self.stream.writeln(
                    '%s (%.3fs)' % (verbose_str, test_info.elapsed_time)
                )
            elif self.dots:
                self.stream.write(short_str)
        self.callback = callback

    def startTest(self, test):
        """
        Called before execute each test method.
        """
        self.start_time = time.time()
        TestResult.startTest(self, test)

        if self.showAll:
            self.stream.write('  ' + self.getDescription(test))
            self.stream.write(" ... ")

    def _save_output_data(self):
        self._stdout_data = sys.stdout.getvalue()
        self._stderr_data = sys.stderr.getvalue()

    def stopTest(self, test):
        """
        Called after execute each test method.
        """
        self._save_output_data()
        # self._stdout_data = sys.stdout.getvalue()
        # self._stderr_data = sys.stderr.getvalue()

        _TextTestResult.stopTest(self, test)
        self.stop_time = time.time()

        if self.callback and callable(self.callback):
            self.callback()
            self.callback = None

    def addSuccess(self, test):
        """
        Called when a test executes successfully.
        """
        self._save_output_data()
        self._prepare_callback(
            _TestInfo(self, test), self.successes, 'OK', '.'
        )

    def addFailure(self, test, err):
        """
        Called when a test method fails.
        """
        self._save_output_data()
        testinfo = _TestInfo(self, test, _TestInfo.FAILURE, err)
        self.failures.append((
            testinfo,
            self._exc_info_to_string(err, test)
        ))
        self._prepare_callback(testinfo, [], 'FAIL', 'F')

    def addError(self, test, err):
        """
        Called when a test method raises an error.
        """
        self._save_output_data()
        testinfo = _TestInfo(self, test, _TestInfo.ERROR, err)
        self.errors.append((
            testinfo,
            self._exc_info_to_string(err, test)
        ))
        self._prepare_callback(testinfo, [], 'ERROR', 'E')

    def addSkip(self, test, reason):
        """
        Called when a test method was skipped.
        """
        self._save_output_data()
        testinfo = _TestInfo(self, test, _TestInfo.SKIP, reason)
        self.skipped.append((testinfo, reason))
        self._prepare_callback(testinfo, [], 'SKIP', 'S')

    def printErrorList(self, flavour, errors):
        """
        Writes information about the FAIL or ERROR to the stream.
        """
        for test_info, error in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln(
                '%s [%.3fs]: %s' % (flavour, test_info.elapsed_time,
                                    test_info.get_description())
            )
            self.stream.writeln(self.separator2)
            self.stream.writeln('%s' % test_info.get_error_info())

    def _get_info_by_testcase(self, outsuffix):
        """
        Organizes test results by TestCase module. This information is
        used during the report generation, where a XML report will be created
        for each TestCase.
        """
        tests_by_testcase = {}

        for tests in (self.successes, self.failures, self.errors, self.skipped):
            for test_info in tests:
                if isinstance(test_info, tuple):
                    # This is a skipped, error or a failure test case
                    test_info = test_info[0]
                testcase_name = test_info.test_name
                if not testcase_name in tests_by_testcase:
                    tests_by_testcase[testcase_name] = []
                tests_by_testcase[testcase_name].append(test_info)

        return tests_by_testcase

    def _report_testsuite_properties(xml_testsuite, xml_document, properties):
        xml_properties = xml_document.createElement('properties')
        xml_testsuite.appendChild(xml_properties)
        if properties:
            for key, value in properties.items():
                prop = xml_document.createElement('property')
                prop.setAttribute('name', str(key))
                prop.setAttribute('value', str(value))
                xml_properties.appendChild(prop)
        return xml_properties

    _report_testsuite_properties = staticmethod(_report_testsuite_properties)

    def _report_testsuite(suite_name, outsuffix, tests, xml_document, properties):
        """
        Appends the testsuite section to the XML document.
        """
        testsuite = xml_document.createElement('testsuite')
        xml_document.appendChild(testsuite)

        testsuite.setAttribute('name', "%s-%s" % (suite_name, outsuffix))
        testsuite.setAttribute('tests', str(len(tests)))

        testsuite.setAttribute(
            'time', '%.3f' % sum(map(lambda e: e.elapsed_time, tests))
        )
        failures = filter(lambda e: e.outcome == _TestInfo.FAILURE, tests)
        testsuite.setAttribute('failures', str(len(list(failures))))

        errors = filter(lambda e: e.outcome == _TestInfo.ERROR, tests)
        testsuite.setAttribute('errors', str(len(list(errors))))

        _XMLTestResult._report_testsuite_properties(testsuite, xml_document, properties)

        systemout = xml_document.createElement('system-out')
        testsuite.appendChild(systemout)

        stdout = StringIO()
        for test in tests:
            # Merge the stdout from the tests in a class
            stdout.write(test.stdout)
        _XMLTestResult._createCDATAsections(xml_document, systemout, stdout.getvalue())

        systemerr = xml_document.createElement('system-err')
        testsuite.appendChild(systemerr)

        stderr = StringIO()
        for test in tests:
            # Merge the stderr from the tests in a class
            stderr.write(test.stderr)
        _XMLTestResult._createCDATAsections(xml_document, systemerr, stderr.getvalue())

        return testsuite

    _report_testsuite = staticmethod(_report_testsuite)

    def _test_method_name(test_id):
        """
        Returns the test method name.
        """
        return test_id.split('.')[-1]

    _test_method_name = staticmethod(_test_method_name)

    def _createCDATAsections(xmldoc, node, text):
        text = safe_unicode(text)
        pos = text.find(']]>')
        while pos >= 0:
            tmp=text[0:pos+2]
            cdata = xmldoc.createCDATASection(tmp)
            node.appendChild(cdata)
            text=text[pos+2:]
            pos = text.find(']]>')
        cdata = xmldoc.createCDATASection(text)
        node.appendChild(cdata)

    _createCDATAsections = staticmethod(_createCDATAsections)


    def _report_testcase(suite_name, test_result, xml_testsuite, xml_document):
        """
        Appends a testcase section to the XML document.
        """
        testcase = xml_document.createElement('testcase')
        xml_testsuite.appendChild(testcase)

        testcase.setAttribute('classname', suite_name)
        testcase.setAttribute(
            'name', _XMLTestResult._test_method_name(test_result.test_id)
        )
        testcase.setAttribute('time', '%.3f' % test_result.elapsed_time)

        if (test_result.outcome != _TestInfo.SUCCESS):
            elem_name = ('failure', 'error', 'skipped')[test_result.outcome - 1]
            failure = xml_document.createElement(elem_name)
            testcase.appendChild(failure)
            if test_result.outcome != _TestInfo.SKIP:
                failure.setAttribute('type', safe_unicode(test_result.err[0].__name__))
                failure.setAttribute('message', safe_unicode(test_result.err[1]))
                error_info = safe_unicode(test_result.get_error_info())
                _XMLTestResult._createCDATAsections(xml_document, failure, error_info)
            else:
                failure.setAttribute('type', 'skip')
                failure.setAttribute('message', safe_unicode(test_result.err))

    _report_testcase = staticmethod(_report_testcase)

    def generate_reports(self, test_runner):
        """
        Generates the XML reports to a given XMLTestRunner object.
        """
        from xml.dom.minidom import Document
        all_results = self._get_info_by_testcase(test_runner.outsuffix)

        if (isinstance(test_runner.output, six.string_types) and not
                os.path.exists(test_runner.output)):
            os.makedirs(test_runner.output)

        for suite, tests in all_results.items():
            doc = Document()

            # Build the XML file
            testsuite = _XMLTestResult._report_testsuite(
                suite, test_runner.outsuffix, tests, doc, self.properties
            )
            for test in tests:
                _XMLTestResult._report_testcase(suite, test, testsuite, doc)
            xml_content = doc.toprettyxml(indent='\t', encoding=test_runner.encoding)

            if isinstance(test_runner.output, six.string_types):
                report_file = open(
                    '%s%sTEST-%s-%s.xml' % (
                        test_runner.output, os.sep, suite,
                        test_runner.outsuffix
                    ), 'wb'
                )
                try:
                    report_file.write(xml_content)
                finally:
                    report_file.close()
            else:
                # Assume that test_runner.output is a stream
                test_runner.output.write(xml_content)
