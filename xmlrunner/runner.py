
import sys
import time

from .unittest import TextTestRunner
from .result import _XMLTestResult, _TestInfo

# see issue #74, the encoding name needs to be one of
# http://www.iana.org/assignments/character-sets/character-sets.xhtml
UTF8 = 'UTF-8'


class XMLTestRunner(TextTestRunner):
    """
    A test runner class that outputs the results in JUnit like XML files.
    """
    def __init__(self, output='.', outsuffix=None, stream=sys.stderr,
                 descriptions=True, verbosity=1, elapsed_times=True,
                 failfast=False, buffer=False, encoding=UTF8, info_cls=_TestInfo):
        TextTestRunner.__init__(self, stream, descriptions, verbosity,
                                failfast=failfast, buffer=buffer)
        self.verbosity = verbosity
        self.output = output
        self.encoding = encoding
        # None means default timestamped suffix
        # '' (empty) means no suffix
        if outsuffix is None:
            outsuffix = time.strftime("%Y%m%d%H%M%S")
        self.outsuffix = outsuffix
        self.elapsed_times = elapsed_times
        if issubclass(info_cls, _TestInfo):
            self.info_cls = info_cls
        else:
            self.info_cls = _TestInfo

    def _make_result(self):
        """
        Creates a TestResult object which will be used to store
        information about the executed tests.
        """
        return _XMLTestResult(
            self.stream, self.descriptions, self.verbosity, self.elapsed_times,
            info_cls=self.info_cls
        )

    def run(self, test):
        """
        Runs the given test case or test suite.
        """
        try:
            # Prepare the test execution
            result = self._make_result()
            result.failfast = self.failfast
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
                infos.append("unexpected successes={0}".format(
                    unexpectedSuccesses))

            if infos:
                self.stream.writeln(" ({0})".format(", ".join(infos)))
            else:
                self.stream.write("\n")

            # Generate reports
            self.stream.writeln()
            self.stream.writeln('Generating XML reports...')
            result.generate_reports(self)
        finally:
            pass

        return result
