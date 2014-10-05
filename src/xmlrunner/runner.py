
import sys
import time

try:
    from unittest2.runner import TextTestRunner
except ImportError:
    from unittest import TextTestRunner

from .result import _XMLTestResult

try:
    # Removed in Python 3
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


class _DelegateIO(object):
    """
    This class defines an object that captures whatever is written to
    a stream or file.
    """

    def __init__(self, delegate):
        self._captured = StringIO()
        self.delegate = delegate

    def write(self, text):
        self._captured.write(text)
        self.delegate.write(text)

    def __getattr__(self, attr):
        try:
            return getattr(self._captured, attr)
        except AttributeError:
            return getattr(self.delegate, attr)

    def reset(self):
        self._captured = StringIO()


class XMLTestRunner(TextTestRunner):
    """
    A test runner class that outputs the results in JUnit like XML files.
    """
    def __init__(self, output='.', outsuffix=None, stream=sys.stderr,
                 descriptions=True, verbosity=1, elapsed_times=True,
                 failfast=False, encoding=None):
        TextTestRunner.__init__(self, stream, descriptions, verbosity,
                                failfast=failfast)
        self.verbosity = verbosity
        self.output = output
        self.encoding = encoding
        if outsuffix:
            self.outsuffix = outsuffix
        else:
            self.outsuffix = time.strftime("%Y%m%d%H%M%S")
        self.elapsed_times = elapsed_times

    def _make_result(self):
        """
        Creates a TestResult object which will be used to store
        information about the executed tests.
        """
        return _XMLTestResult(
            self.stream, self.descriptions, self.verbosity, self.elapsed_times
        )

    def _patch_standard_output(self):
        """
        Replaces stdout and stderr streams with string-based streams
        in order to capture the tests' output.
        """
        sys.stdout = _DelegateIO(sys.stdout)
        sys.stderr = _DelegateIO(sys.stderr)

    def _restore_standard_output(self):
        """
        Restores stdout and stderr streams.
        """
        sys.stdout = sys.stdout.delegate
        sys.stderr = sys.stderr.delegate

    def run(self, test):
        """
        Runs the given test case or test suite.
        """
        try:
            # Prepare the test execution
            self._patch_standard_output()
            result = self._make_result()
            if hasattr(test, 'properties'):
                # junit testsuite properties
                result.properties = test.properties

            # Print a nice header
            self.stream.writeln()
            self.stream.writeln('Running tests...')
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
            self.stream.writeln("Ran %d test%s in %.3fs" % (
                run, run != 1 and "s" or "", time_taken)
            )
            self.stream.writeln()

            expectedFails = unexpectedSuccesses = skipped = 0
            try:
                results = map(len, (result.expectedFailures,
                                    result.unexpectedSuccesses,
                                    result.skipped))
            except AttributeError:
                pass
            else:
                expectedFails, unexpectedSuccesses, skipped = results

            # Error traces
            infos = []
            if not result.wasSuccessful():
                self.stream.write("FAILED")
                failed, errored = map(len, (result.failures, result.errors))
                if failed:
                    infos.append("failures={0}".format(failed))
                if errored:
                    infos.append("errors={0}".format(errored))
            else:
                self.stream.write("OK")

            if skipped:
                infos.append("skipped={0}".format(skipped))
            if expectedFails:
                infos.append("expected failures={0}".format(expectedFails))
            if unexpectedSuccesses:
                infos.append("unexpected successes={0}".format(unexpectedSuccesses))

            if infos:
                self.stream.writeln(" ({0})".format(", ".join(infos)))
            else:
                self.stream.write("\n")

            # Generate reports
            self.stream.writeln()
            self.stream.writeln('Generating XML reports...')
            result.generate_reports(self)
        finally:
            self._restore_standard_output()

        return result
