
import io
import os
import sys
import datetime
import time
import traceback
import six
import re
from os import path
from six.moves import StringIO

from .unittest import TestResult, _TextTestResult, failfast


# Matches invalid XML1.0 unicode characters, like control characters:
# http://www.w3.org/TR/2006/REC-xml-20060816/#charsets
# http://stackoverflow.com/questions/1707890/fast-way-to-filter-illegal-xml-unicode-chars-in-python

_illegal_unichrs = [
    (0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F),
    (0x7F, 0x84), (0x86, 0x9F),
    (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF),
]
if sys.maxunicode >= 0x10000:  # not narrow build
    _illegal_unichrs.extend([
        (0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF),
        (0x3FFFE, 0x3FFFF), (0x4FFFE, 0x4FFFF),
        (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
        (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF),
        (0x9FFFE, 0x9FFFF), (0xAFFFE, 0xAFFFF),
        (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
        (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF),
        (0xFFFFE, 0xFFFFF), (0x10FFFE, 0x10FFFF),
    ])

_illegal_ranges = [
    "%s-%s" % (six.unichr(low), six.unichr(high))
    for (low, high) in _illegal_unichrs
]

INVALID_XML_1_0_UNICODE_RE = re.compile(u'[%s]' % u''.join(_illegal_ranges))


STDOUT_LINE = '\nStdout:\n%s'
STDERR_LINE = '\nStderr:\n%s'


def _to_unicode(data):
    """Returns unicode in Python2 and str in Python3"""
    if six.PY3:
        return six.text_type(data)
    try:
        # Try utf8
        return six.text_type(data)
    except UnicodeDecodeError:
        return repr(data).decode('utf8', 'replace')


def safe_unicode(data, encoding='utf8'):
    """Return a unicode string containing only valid XML characters.

    encoding - if data is a byte string it is first decoded to unicode
        using this encoding.
    """
    data = _to_unicode(data)
    if isinstance(data, six.binary_type):
        # e.g. IronPython, see #182
        data = data.decode(encoding)
    return INVALID_XML_1_0_UNICODE_RE.sub('', data)


def testcase_name(test_method):
    testcase = type(test_method)

    # Ignore module name if it is '__main__'
    module = testcase.__module__ + '.'
    if module == '__main__.':
        module = ''
    result = module + testcase.__name__
    return result


class _DuplicateWriter(io.TextIOBase):
    """
    Duplicate output from the first handle to the second handle

    The second handle is expected to be a StringIO and not to block.
    """

    def __init__(self, first, second):
        super(_DuplicateWriter, self).__init__()
        self._first = first
        self._second = second

    def flush(self):
        self._first.flush()
        self._second.flush()

    def writable(self):
        return True

    def writelines(self, lines):
        self._first.writelines(lines)
        self._second.writelines(lines)

    def write(self, b):
        if isinstance(self._first, io.TextIOBase):
            wrote = self._first.write(b)

            if wrote is not None:
                # expected to always succeed to write
                self._second.write(b[:wrote])

            return wrote
        else:
            # file-like object in Python2
            # It doesn't return wrote bytes.
            self._first.write(b)
            self._second.write(b)
            return len(b)


class _TestInfo(object):
    """
    This class keeps useful information about the execution of a
    test method.
    """

    # Possible test outcomes
    (SUCCESS, FAILURE, ERROR, SKIP) = range(4)

    def __init__(self, test_result, test_method, outcome=SUCCESS, err=None, subTest=None):
        self.test_result = test_result
        self.outcome = outcome
        self.elapsed_time = 0
        self.timestamp = datetime.datetime.min.replace(microsecond=0).isoformat()
        if err is not None:
            if self.outcome != _TestInfo.SKIP:
                self.test_exception_name = safe_unicode(err[0].__name__)
                self.test_exception_message = safe_unicode(err[1])
            else:
                self.test_exception_message = safe_unicode(err)

        self.stdout = test_result._stdout_data
        self.stderr = test_result._stderr_data

        self.test_description = self.test_result.getDescription(test_method)
        self.test_exception_info = (
            '' if outcome in (self.SUCCESS, self.SKIP)
            else self.test_result._exc_info_to_string(
                    err, test_method)
        )

        self.test_name = testcase_name(test_method)
        self.test_id = test_method.id()
        self.subDescription = None
        if subTest:
            self.test_id = subTest.id()
            self.subDescription = subTest._subDescription()

    def id(self):
        return self.test_id

    def test_finished(self):
        """Save info that can only be calculated once a test has run.
        """
        self.elapsed_time = \
            self.test_result.stop_time - self.test_result.start_time
        timestamp = datetime.datetime.fromtimestamp(self.test_result.stop_time)
        self.timestamp = timestamp.replace(microsecond=0).isoformat()

    def get_description(self):
        """
        Return a text representation of the test method.
        """
        description = self.test_description

        if self.subDescription is not None:
            description += ' ' + self.subDescription

        return description

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
                 elapsed_times=True, properties=None, infoclass=None):
        _TextTestResult.__init__(self, stream, descriptions, verbosity)
        self._stdout_data = None
        self._stderr_data = None
        self._stdout_capture = StringIO()
        self.__stdout_saved = None
        self._stderr_capture = StringIO()
        self.__stderr_saved = None
        self.successes = []
        self.callback = None
        self.elapsed_times = elapsed_times
        self.properties = properties  # junit testsuite properties
        if infoclass is None:
            self.infoclass = _TestInfo
        else:
            self.infoclass = infoclass

    def _prepare_callback(self, test_info, target_list, verbose_str,
                          short_str):
        """
        Appends a `infoclass` to the given target list and sets a callback
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

            self.stream.flush()

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
            self.stream.flush()

    def _setupStdout(self):
        """
        Capture stdout / stderr by replacing sys.stdout / sys.stderr
        """
        super(_XMLTestResult, self)._setupStdout()
        self.__stdout_saved = sys.stdout
        sys.stdout = _DuplicateWriter(sys.stdout, self._stdout_capture)
        self.__stderr_saved = sys.stderr
        sys.stderr = _DuplicateWriter(sys.stderr, self._stderr_capture)

    def _restoreStdout(self):
        """
        Stop capturing stdout / stderr and recover sys.stdout / sys.stderr
        """
        if self.__stdout_saved:
            sys.stdout = self.__stdout_saved
            self.__stdout_saved = None
        if self.__stderr_saved:
            sys.stderr = self.__stderr_saved
            self.__stderr_saved = None
        self._stdout_capture.seek(0)
        self._stdout_capture.truncate()
        self._stderr_capture.seek(0)
        self._stderr_capture.truncate()
        super(_XMLTestResult, self)._restoreStdout()

    def _save_output_data(self):
        self._stdout_data = self._stdout_capture.getvalue()
        self._stderr_data = self._stderr_capture.getvalue()

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
            self.infoclass(self, test), self.successes, 'OK', '.'
        )

    @failfast
    def addFailure(self, test, err):
        """
        Called when a test method fails.
        """
        self._save_output_data()
        testinfo = self.infoclass(
            self, test, self.infoclass.FAILURE, err)
        self.failures.append((
            testinfo,
            self._exc_info_to_string(err, test)
        ))
        self._prepare_callback(testinfo, [], 'FAIL', 'F')

    @failfast
    def addError(self, test, err):
        """
        Called when a test method raises an error.
        """
        self._save_output_data()
        testinfo = self.infoclass(
            self, test, self.infoclass.ERROR, err)
        self.errors.append((
            testinfo,
            self._exc_info_to_string(err, test)
        ))
        self._prepare_callback(testinfo, [], 'ERROR', 'E')

    def addSubTest(self, testcase, test, err):
        """
        Called when a subTest method raises an error.
        """
        if err is not None:

            errorText = None
            errorValue = None
            errorList = None
            if issubclass(err[0], test.failureException):
                errorText = 'FAIL'
                errorValue = self.infoclass.FAILURE
                errorList = self.failures

            else:
                errorText = 'ERROR'
                errorValue = self.infoclass.ERROR
                errorList = self.errors

            self._save_output_data()

            testinfo = self.infoclass(
                self, testcase, errorValue, err, subTest=test)
            errorList.append((
                testinfo,
                self._exc_info_to_string(err, testcase)
            ))
            self._prepare_callback(testinfo, [], errorText, errorText[0])

    def addSkip(self, test, reason):
        """
        Called when a test method was skipped.
        """
        self._save_output_data()
        testinfo = self.infoclass(
            self, test, self.infoclass.SKIP, reason)
        self.skipped.append((testinfo, reason))
        self._prepare_callback(testinfo, [], 'SKIP', 'S')

    def addExpectedFailure(self, test, err):
        """
        Missing in xmlrunner, copy-pasted from xmlrunner addError.
        """
        self._save_output_data()

        testinfo = self.infoclass(self, test, self.infoclass.ERROR, err)
        testinfo.test_exception_name = 'ExpectedFailure'
        testinfo.test_exception_message = 'EXPECTED FAILURE: {}'.format(testinfo.test_exception_message)

        self.expectedFailures.append((testinfo, self._exc_info_to_string(err, test)))
        self._prepare_callback(testinfo, [], 'EXPECTED FAILURE', 'X')

    @failfast
    def addUnexpectedSuccess(self, test):
        """
        Missing in xmlrunner, copy-pasted from xmlrunner addSuccess.
        """
        self._save_output_data()

        testinfo = self.infoclass(self, test)  # do not set outcome here because it will need exception
        testinfo.outcome = self.infoclass.ERROR
        # But since we want to have error outcome, we need to provide additional fields:
        testinfo.test_exception_name = 'UnexpectedSuccess'
        testinfo.test_exception_message = ('UNEXPECTED SUCCESS: This test was marked as expected failure but passed, '
                                           'please review it')

        self.unexpectedSuccesses.append(testinfo)
        self._prepare_callback(testinfo, [], 'UNEXPECTED SUCCESS', 'U')

    def printErrorList(self, flavour, errors):
        """
        Writes information about the FAIL or ERROR to the stream.
        """
        for test_info, dummy in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln(
                '%s [%.3fs]: %s' % (flavour, test_info.elapsed_time,
                                    test_info.get_description())
            )
            self.stream.writeln(self.separator2)
            self.stream.writeln('%s' % test_info.get_error_info())
            self.stream.flush()

    def _get_info_by_testcase(self):
        """
        Organizes test results by TestCase module. This information is
        used during the report generation, where a XML report will be created
        for each TestCase.
        """
        tests_by_testcase = {}

        for tests in (self.successes, self.failures, self.errors,
                      self.skipped, self.expectedFailures, self.unexpectedSuccesses):
            for test_info in tests:
                if isinstance(test_info, tuple):
                    # This is a skipped, error or a failure test case
                    test_info = test_info[0]
                testcase_name = test_info.test_name
                if testcase_name not in tests_by_testcase:
                    tests_by_testcase[testcase_name] = []
                tests_by_testcase[testcase_name].append(test_info)

        return tests_by_testcase

    def _report_testsuite_properties(xml_testsuite, xml_document, properties):
        if properties:
            xml_properties = xml_document.createElement('properties')
            xml_testsuite.appendChild(xml_properties)
            for key, value in properties.items():
                prop = xml_document.createElement('property')
                prop.setAttribute('name', str(key))
                prop.setAttribute('value', str(value))
                xml_properties.appendChild(prop)

    _report_testsuite_properties = staticmethod(_report_testsuite_properties)

    def _report_testsuite(suite_name, tests, xml_document, parentElement,
                          properties):
        """
        Appends the testsuite section to the XML document.
        """
        testsuite = xml_document.createElement('testsuite')
        parentElement.appendChild(testsuite)
        module_name = suite_name.rpartition('.')[0]
        file_name = module_name.replace('.', '/') + '.py'

        testsuite.setAttribute('name', suite_name)
        testsuite.setAttribute('tests', str(len(tests)))
        testsuite.setAttribute('file', file_name)

        testsuite.setAttribute(
            'time', '%.3f' % sum(map(lambda e: e.elapsed_time, tests))
        )
        if tests:
            testsuite.setAttribute(
                'timestamp', max(map(lambda e: e.timestamp, tests))
            )
        failures = filter(lambda e: e.outcome == e.FAILURE, tests)
        testsuite.setAttribute('failures', str(len(list(failures))))

        errors = filter(lambda e: e.outcome == e.ERROR, tests)
        testsuite.setAttribute('errors', str(len(list(errors))))

        skips = filter(lambda e: e.outcome == _TestInfo.SKIP, tests)
        testsuite.setAttribute('skipped', str(len(list(skips))))

        _XMLTestResult._report_testsuite_properties(
            testsuite, xml_document, properties)

        for test in tests:
            _XMLTestResult._report_testcase(test, testsuite, xml_document)

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
            tmp = text[0:pos+2]
            cdata = xmldoc.createCDATASection(tmp)
            node.appendChild(cdata)
            text = text[pos+2:]
            pos = text.find(']]>')
        cdata = xmldoc.createCDATASection(text)
        node.appendChild(cdata)

    _createCDATAsections = staticmethod(_createCDATAsections)

    def _report_testcase(test_result, xml_testsuite, xml_document):
        """
        Appends a testcase section to the XML document.
        """
        testcase = xml_document.createElement('testcase')
        xml_testsuite.appendChild(testcase)

        class_name = re.sub(r'^__main__.', '', test_result.id())
        class_name = class_name.rpartition('.')[0]
        testcase.setAttribute('classname', class_name)
        testcase.setAttribute(
            'name', _XMLTestResult._test_method_name(test_result.test_id)
        )
        testcase.setAttribute('time', '%.3f' % test_result.elapsed_time)
        testcase.setAttribute('timestamp', test_result.timestamp)

        if (test_result.outcome != test_result.SUCCESS):
            elem_name = ('failure', 'error', 'skipped')[test_result.outcome-1]
            failure = xml_document.createElement(elem_name)
            testcase.appendChild(failure)
            if test_result.outcome != test_result.SKIP:
                failure.setAttribute(
                    'type',
                    test_result.test_exception_name
                )
                failure.setAttribute(
                    'message',
                    test_result.test_exception_message
                )
                error_info = safe_unicode(test_result.get_error_info())
                _XMLTestResult._createCDATAsections(
                    xml_document, failure, error_info)
            else:
                failure.setAttribute('type', 'skip')
                failure.setAttribute('message', test_result.test_exception_message)

        if test_result.stdout:
            systemout = xml_document.createElement('system-out')
            testcase.appendChild(systemout)
            _XMLTestResult._createCDATAsections(
                xml_document, systemout, test_result.stdout)

        if test_result.stderr:
            systemout = xml_document.createElement('system-err')
            testcase.appendChild(systemout)
            _XMLTestResult._createCDATAsections(
                xml_document, systemout, test_result.stderr)

    _report_testcase = staticmethod(_report_testcase)

    def generate_reports(self, test_runner):
        """
        Generates the XML reports to a given XMLTestRunner object.
        """
        from xml.dom.minidom import Document
        all_results = self._get_info_by_testcase()

        outputHandledAsString = \
            isinstance(test_runner.output, six.string_types)

        if (outputHandledAsString and not os.path.exists(test_runner.output)):
            os.makedirs(test_runner.output)

        if not outputHandledAsString:
            doc = Document()
            testsuite = doc.createElement('testsuites')
            doc.appendChild(testsuite)
            parentElement = testsuite

        for suite, tests in all_results.items():
            if outputHandledAsString:
                doc = Document()
                parentElement = doc

            suite_name = suite
            if test_runner.outsuffix:
                # not checking with 'is not None', empty means no suffix.
                suite_name = '%s-%s' % (suite, test_runner.outsuffix)

            # Build the XML file
            testsuite = _XMLTestResult._report_testsuite(
                suite_name, tests, doc, parentElement, self.properties
            )

            if outputHandledAsString:
                xml_content = doc.toprettyxml(
                    indent='\t',
                    encoding=test_runner.encoding
                )
                filename = path.join(
                    test_runner.output,
                    'TEST-%s.xml' % suite_name)
                with open(filename, 'wb') as report_file:
                    report_file.write(xml_content)

                self.stream.writeln('Generated XML report: {}'.format(filename))

        if not outputHandledAsString:
            # Assume that test_runner.output is a stream
            xml_content = doc.toprettyxml(
                indent='\t',
                encoding=test_runner.encoding
            )
            test_runner.output.write(xml_content)

    def _exc_info_to_string(self, err, test):
        """Converts a sys.exc_info()-style tuple of values into a string."""
        if six.PY3:
            # It works fine in python 3
            try:
                return super(_XMLTestResult, self)._exc_info_to_string(
                    err, test)
            except AttributeError:
                # We keep going using the legacy python <= 2 way
                pass

        # This comes directly from python2 unittest
        exctype, value, tb = err
        # Skip test runner traceback levels
        while tb and self._is_relevant_tb_level(tb):
            tb = tb.tb_next

        if exctype is test.failureException:
            # Skip assert*() traceback levels
            length = self._count_relevant_tb_levels(tb)
            msgLines = traceback.format_exception(exctype, value, tb, length)
        else:
            msgLines = traceback.format_exception(exctype, value, tb)

        if self.buffer:
            output = self._stdout_capture.getvalue()
            error = self._stdout_capture.getvalue()
            if output:
                if not output.endswith('\n'):
                    output += '\n'
                msgLines.append(STDOUT_LINE % output)
            if error:
                if not error.endswith('\n'):
                    error += '\n'
                msgLines.append(STDERR_LINE % error)
        # This is the extra magic to make sure all lines are str
        encoding = getattr(sys.stdout, 'encoding', 'utf-8')
        lines = []
        for line in msgLines:
            if not isinstance(line, str):
                # utf8 shouldnt be hard-coded, but not sure f
                line = line.encode(encoding)
            lines.append(line)

        return ''.join(lines)
