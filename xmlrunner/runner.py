import argparse
import sys
import os
import time
import inspect

from .unittest import TextTestRunner, TestProgram
from .result import _XMLTestResult

# ---------------------------------------------------
from xmlrunner.allure_report.hook import AllureHook

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
        self.allure_hook = AllureHook()
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

    def _make_result(self, **kwargs):
        """
        Creates a TestResult object which will be used to store
        information about the executed tests.
        """
        if kwargs.get("domain", None) and kwargs.get("file_name", None):
            return self.resultclass(
                kwargs["file_name"], kwargs["domain"], self.stream, self.descriptions, self.verbosity,
                self.elapsed_times
            )
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
            test_runner = test._tests[-1]._tests[0]
            file_name = os.path.basename(inspect.getfile(type(test_runner))).split(".")[0]
            domain = test_runner.DOMAIN
            if domain is None:
                domain = "Default"
            result = self._make_result(file_name=file_name, domain=domain)
            result.failfast = self.failfast
            result.buffer = self.buffer
            if hasattr(test, 'properties'):
                # junit testsuite properties
                result.properties = test.properties

            # Print a nice header
            self.stream.writeln()
            self.stream.writeln('Running tests...')
            self.stream.writeln(result.separator2)

            # Running allure report
            self.allure_hook.register_allure_plugins(test, file_name, domain)

            # Execute tests
            start_time = time.monotonic()
            test(result)
            stop_time = time.monotonic()
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
            self.stream.writeln('Generating XML and allure reports...')

            result.generate_reports(self)
        finally:
            # Unregister allure hook to generate allure report result
            self.allure_hook.unregister_allure_plugins()
            pass

        return result


class XMLTestProgram(TestProgram):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('testRunner', XMLTestRunner)
        self.warnings = None  # python2 fix
        self._parseKnownArgs(kwargs)
        super(XMLTestProgram, self).__init__(*args, **kwargs)

    def _parseKnownArgs(self, kwargs):
        argv = kwargs.get('argv')
        if argv is None:
            argv = sys.argv

        # python2 argparse fix
        parser = argparse.ArgumentParser(prog='xmlrunner')
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '-o', '--output', metavar='DIR',
            help='Directory for storing XML reports (\'.\' default)')
        group.add_argument(
            '--output-file', metavar='FILENAME',
            help='Filename for storing XML report')
        parser.add_argument(
            '--outsuffix', metavar='STRING',
            help='Output suffix (timestamp is default)')
        namespace, argv = parser.parse_known_args(argv)
        self.output = namespace.output
        self.output_file = namespace.output_file
        self.outsuffix = namespace.outsuffix
        kwargs['argv'] = argv

    def _initArgParsers(self):
        # this code path is only called in python3 (optparse vs argparse)
        super(XMLTestProgram, self)._initArgParsers()

        for parser in (self._main_parser, self._discovery_parser):
            group = parser.add_mutually_exclusive_group()
            group.add_argument(
                '-o', '--output', metavar='DIR', nargs=1,
                help='Directory for storing XML reports (\'.\' default)')
            group.add_argument(
                '--output-file', metavar='FILENAME', nargs=1,
                help='Filename for storing XML report')
            group.add_argument(
                '--outsuffix', metavar='STRING', nargs=1,
                help='Output suffix (timestamp is default)')

    def runTests(self):
        kwargs = dict(
            verbosity=self.verbosity,
            failfast=self.failfast,
            buffer=self.buffer,
            warnings=self.warnings,
        )
        if sys.version_info[:2] > (3, 4):
            kwargs.update(tb_locals=self.tb_locals)

        output_file = None
        try:
            if self.output_file is not None:
                output_file = open(self.output_file, 'wb')
                kwargs.update(output=output_file)
            elif self.output is not None:
                kwargs.update(output=self.output)

            if self.outsuffix is not None:
                kwargs.update(outsuffix=self.outsuffix)

            self.testRunner = self.testRunner(**kwargs)
            super(XMLTestProgram, self).runTests()
        finally:
            if output_file is not None:
                output_file.close()
