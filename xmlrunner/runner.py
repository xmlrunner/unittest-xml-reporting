
import sys
import time

from .unittest import TextTestRunner, TestProgram
from .result import _XMLTestResult

# see issue #74, the encoding name needs to be one of
# http://www.iana.org/assignments/character-sets/character-sets.xhtml
UTF8 = 'UTF-8'


class XMLTestRunner(TextTestRunner):
    """
    A test runner class that outputs the results in JUnit like XML files.
    """
    def __init__(self, output='.', outsuffix=None, 
                 elapsed_times=True, encoding=UTF8,
                 resultclass=None,
                 **kwargs):
        super(XMLTestRunner, self).__init__(**kwargs)
        self.output = output
        self.encoding = encoding
        # None means default timestamped suffix
        # '' (empty) means no suffix
        if outsuffix is None:
            outsuffix = time.strftime("%Y%m%d%H%M%S")
        self.outsuffix = outsuffix
        self.elapsed_times = elapsed_times
        if resultclass is None:
            self.resultclass = _XMLTestResult
        else:
            self.resultclass = resultclass

    def _make_result(self):
        """
        Creates a TestResult object which will be used to store
        information about the executed tests.
        """
        # override in subclasses if necessary.
        return self.resultclass(
            self.stream, self.descriptions, self.verbosity, self.elapsed_times
        )

    def run(self, test):
        """
        Runs the given test case or test suite.
        """
        try:
            # Prepare the test execution
            result = self._make_result()
            result.failfast = self.failfast
            result.buffer = self.buffer
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

            # other metrics
            expectedFails = len(result.expectedFailures)
            unexpectedSuccesses = len(result.unexpectedSuccesses)
            skipped = len(result.skipped)

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


class XMLTestProgram(TestProgram):
    output = None

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('testRunner', XMLTestRunner)
        super(XMLTestProgram, self).__init__(*args, **kwargs)

    def _initArgParsers(self):
        super(XMLTestProgram, self)._initArgParsers()

        for parser in (self._main_parser, self._discovery_parser):
            parser.add_argument('-o', '--output', metavar='DIR',
                                help='Directory for storing XML reports '
                                "('.' default)")

    def runTests(self):
        if self.output is not None:
            kwargs = dict(verbosity=self.verbosity,
                          failfast=self.failfast,
                          buffer=self.buffer,
                          warnings=self.warnings,
                          output=self.output)

            if sys.version_info[:2] > (3, 4):
                kwargs.update(tb_locals=self.tb_locals)

            self.testRunner = self.testRunner(**kwargs)

        super(XMLTestProgram, self).runTests()
