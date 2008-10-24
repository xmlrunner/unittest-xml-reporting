"""
This is a Python unittest-based test runner that can export test results to
JUnit like XML reporting.

Author: Daniel Fernandes Martins <daniel.tritone@gmail.com>
"""

import os
import sys
import time
from unittest import TestResult, _TextTestResult, TextTestRunner
from xml.dom.minidom import Document
from StringIO import StringIO


class TestInfo(object):
    """This class is used to keep useful information about the execution of a
    test method.
    """
    (SUCCESS, FAILURE, ERROR) = range(3)
    
    def __init__(self, test_result, test, outcome=SUCCESS, err=None):
        "Create a new instance of TestInfo."
        self.test_result = test_result
        self.test = test
        self.outcome = outcome
        self.err = err
    
    def get_elapsed_time(self):
        "Return the time that shows how long the test method took to execute."
        return self.test_result.stop_time - self.test_result.start_time
    
    def get_description(self):
        "Return a text representation of the test method."
        return self.test_result.getDescription(self.test)
    
    def get_error_info(self):
        "Return a text representation of an exception thrown by a test method."
        if not self.err:
            return ''
        return self.test_result._exc_info_to_string(self.err, self.test)


class _XMLTestResult(_TextTestResult):
    """A test result class that can express test results in a XML report.

    Used by XMLTestRunner.
    """
    def __init__(self, stream, descriptions, verbosity):
        """Create a new instance of _XMLTestResult.
        
        Used by XMLTestRunner.
        """
        _TextTestResult.__init__(self, stream, descriptions, verbosity)
        self.successes = []
        self.callback = None
    
    def _prepare_callback(self, test_info, target_list, \
        verbose_str, short_str):
        """Append a TestInfo to the given target list and sets a callback
        method to be called by stopTest method.
        """
        target_list.append(test_info)
        def callback():
            """This callback prints the test method outcome to the stream,
            as well as the elapsed time.
            """
            if self.showAll:
                self.stream.writeln('%s (%.3fs)' % \
                    (verbose_str, test_info.get_elapsed_time()))
            elif self.dots:
                self.stream.write(short_str)
        self.callback = callback
    
    def startTest(self, test):
        "Called before execute each test method."
        self.start_time = time.time()
        TestResult.startTest(self, test)
        
        if self.showAll:
            self.stream.write('   ' + self.getDescription(test))
            self.stream.write(" ... ")
    
    def stopTest(self, test):
        "Called after execute each test method."
        _TextTestResult.stopTest(self, test)
        self.stop_time = time.time()
        if self.callback and callable(self.callback):
            self.callback()
            self.callback = None
    
    def addSuccess(self, test):
        "Called when a test executes successfully."
        self._prepare_callback(TestInfo(self, test), \
            self.successes, 'OK', '.')
    
    def addFailure(self, test, err):
        "Called when a test method fails."
        self._prepare_callback(TestInfo(self, test, 1, err), \
            self.failures, 'FAIL', 'F')
    
    def addError(self, test, err):
        "Called when a test method raises an error."
        self._prepare_callback(TestInfo(self, test, 2, err), \
            self.errors, 'ERROR', 'E')
    
    def printErrorList(self, flavour, errors):
        "Write some information about the FAIL or ERROR to the stream."
        for test_info in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln("%s [%.3fs]: %s" % \
                (flavour, test_info.get_elapsed_time(), \
                test_info.get_description()))
            self.stream.writeln(self.separator2)
            self.stream.writeln("%s" % test_info.get_error_info())
    
    def _get_info_by_testcase(self):
        """This method organizes test results by TestCase. This information
        is used during the report generation, where a XML report will be
        generated for each TestCase.
        """
        tests_by_testcase = {}
        
        for tests in (self.successes, self.failures, self.errors):
            for test_info in tests:
                testcase = type(test_info.test)
                testcase_name = testcase.__module__ + '.' + testcase.__name__
                if not tests_by_testcase.has_key(testcase_name):
                    tests_by_testcase[testcase_name] = []
                tests_by_testcase[testcase_name].append(test_info)
        
        return tests_by_testcase
    
    def generate_reports(self, test_runner):
        "Generates the XML reports to a given XMLTestRunner object."
        all_results = self._get_info_by_testcase()
        if not os.path.exists(test_runner.output_dir):
            os.makedirs(test_runner.output_dir)
        
        for suite, tests in all_results.items():
            doc = Document()
            testsuite = doc.createElement('testsuite')
            doc.appendChild(testsuite)
            testsuite.setAttribute('name', suite)
            testsuite.setAttribute('tests', str(len(tests)))
            failures = filter(lambda e: e.outcome==TestInfo.FAILURE, tests)
            testsuite.setAttribute('failures', str(len(failures)))
            errors = filter(lambda e: e.outcome==TestInfo.ERROR, tests)
            testsuite.setAttribute('errors', str(len(errors)))
            testsuite.setAttribute('time', '%.3f' % \
                sum(map(lambda e: e.get_elapsed_time(), tests)))
            
            for test in tests:
                testcase = doc.createElement('testcase')
                testsuite.appendChild(testcase)
                testcase.setAttribute('classname', suite)
                testcase.setAttribute('name', test.test._testMethodName)
                testcase.setAttribute('time', '%.3f' % test.get_elapsed_time())
                
                if (test.outcome != TestInfo.SUCCESS):
                    elem_name = ['failure', 'error'][test.outcome-1]
                    failure = doc.createElement(elem_name)
                    testcase.appendChild(failure)
                    failure.setAttribute('type', test.err[0].__name__)
                    failure.setAttribute('message', test.err[1].message)
                    error_info = test.get_error_info()
                    failureText = doc.createCDATASection(error_info)
                    failure.appendChild(failureText)
            
            systemout = doc.createElement('system-out')
            testsuite.appendChild(systemout)
            stdout = test_runner.stdout.getvalue()
            systemout_text = doc.createCDATASection(stdout)
            systemout.appendChild(systemout_text)
            
            systemerr = doc.createElement('system-err')
            testsuite.appendChild(systemerr)
            stderr = test_runner.stderr.getvalue()
            systemerr_text = doc.createCDATASection(stderr)
            systemerr.appendChild(systemerr_text)
            
            report_file = file('%s%sTEST-%s.xml' % \
                (test_runner.output_dir, os.sep, suite), 'w')
            report_file.write(doc.toprettyxml(indent='\t'))
            report_file.close()


class XMLTestRunner(TextTestRunner):
    """A test runner class that outputs the results in JUnit like XML files.
    """
    
    def __init__(self, output_dir, stream=sys.stderr, descriptions=1, \
        verbose=False):
        "Create a new instance of XMLTestRunner."
        verbosity = (1, 2)[verbose]
        TextTestRunner.__init__(self, stream, descriptions, verbosity)
        self.output_dir = output_dir
    
    def _make_result(self):
        """Create the TestResult object which will be used to store
        information about the executed tests.
        """
        return _XMLTestResult(self.stream, self.descriptions, \
            self.verbosity)
    
    def _patch_standard_output(self):
        """Replace the stdout and stderr streams with string-based streams
        in order to capture the tests' output.
        """
        (self.old_stdout, self.old_stderr) = (sys.stdout, sys.stderr)
        (self.stdout, self.stderr) = (StringIO(), StringIO())
    
    def _restore_standard_output(self):
        "Restore the stdout and stderr streams."
        (sys.stdout, sys.stderr) = (self.old_stdout, self.old_stderr)
    
    def run(self, test):
        "Run the given test case or test suite."
        
        try:
            self._patch_standard_output()
            result = self._make_result()
            
            # Print a nice header
            self.stream.writeln()
            self.stream.writeln('Running the tests...')
            self.stream.writeln(result.separator2)
            
            # Execute tests
            start_time = time.time()
            test(result)
            stop_time = time.time()
            time_taken = stop_time - start_time
            
            # Print results
            result.printErrors()
            self.stream.writeln(result.separator2)
            run = result.testsRun
            self.stream.writeln("Ran %d test%s in %.3fs" %
                (run, run != 1 and "s" or "", time_taken))
            self.stream.writeln()
            
            # Error traces
            if not result.wasSuccessful():
                self.stream.write("FAILED (")
                failed, errored = (len(result.failures), len(result.errors))
                if failed:
                    self.stream.write("failures=%d" % failed)
                if errored:
                    if failed:
                        self.stream.write(", ")
                    self.stream.write("errors=%d" % errored)
                self.stream.writeln(")")
            else:
                self.stream.writeln("OK")
        finally:
            self._restore_standard_output()
        
        # Generate reports
        self.stream.writeln()
        self.stream.writeln('Generating XML reports...')
        result.generate_reports(self)
        
        return result
