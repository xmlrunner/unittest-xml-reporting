import unittest

__all__ = ('CompositeTestResult',)


class CompositeTestResult(unittest.TestResult):
    """This class defines an aggregation of `TestResult` instances.

    This abstraction is useful because it enables auxiliary `TestResults` to be
    used together with any `TestRunner`/`TestResult` pair. For instance, if you
    are happy with the default `TestRunner`/`TestResult` classes but want to
    plug an auxiliary `TestResult` to the mix (i.e. one capable of generating
    XML-based reports :-), this class provides just that.

    Please refer to `xmlrunner.runner.XMLTestRunner` in order to see how this
    class can be used to generate a mixed TestRunner.
    """

    def __init__(self, delegate, extra=None, stream=None, descriptions=False,
            verbosity=None):
        """Creates an instance of `CompositeTestResult` that forwards calls to
        `TestResult` public interface to `delegate` and the `extra` delegates.

        The `TestResult` specified in `delegate` must be carefully chosen in
        order to match the `TestRunner` being used to run the tests. For
        instance, if you are using `TextTestRunner`, then `delegate` must be an
        instance of `TextTestResult`.
        """
        super(CompositeTestResult, self).__init__(stream=stream,
            descriptions=descriptions, verbosity=verbosity)

        self.delegate = delegate
        self.all_delegates = [delegate] + (extra or [])

    def __getattr__(self, attr):
        """All attributes not defined by this class are forwarded by the
        `TestResult` defined in `self.delegate`.
        """
        return getattr(self.delegate, attr)

    def _call_delegates(self, method_name, *args, **kwargs):
        """Calls `method_name` with the given args on all delegates.
        Returns `None`.
        """
        for delegate in self.all_delegates:
            getattr(delegate, method_name)(*args, **kwargs)

    # From now on, we have all public methods of TestResult being forwarded to
    # all delegates

    def startTestRun(self):
        super(CompositeTestResult, self).startTestRun()
        self._call_delegates('startTestRun')

    def stopTestRun(self):
        super(CompositeTestResult, self).stopTestRun()
        self._call_delegates('stopTestRun')

    def startTest(self, test):
        super(CompositeTestResult, self).startTest(test)
        self._call_delegates('startTest', test)

    def stopTest(self, test):
        super(CompositeTestResult, self).stopTest(test)
        self._call_delegates('stopTest', test)

    def printErrors(self):
        super(CompositeTestResult, self).printErrors()
        self._call_delegates('printErrors')

    def addError(self, test, err):
        super(CompositeTestResult, self).addError(test, err)
        self._call_delegates('addError', test, err)

    def addFailure(self, test, err):
        super(CompositeTestResult, self).addFailure(test, err)
        self._call_delegates('addFailure', test, err)

    def addSuccess(self, test):
        super(CompositeTestResult, self).addSuccess(test)
        self._call_delegates('addSuccess', test)

    def addSkip(self, test, reason):
        super(CompositeTestResult, self).addSkip(test, reason)
        self._call_delegates('addSkip', test, reason)

    def addExpectedFailure(self, test, err):
        super(CompositeTestResult, self).addExpectedFailure(test, err)
        self._call_delegates('addExpectedFailure', test, err)

    def addUnexpectedSuccess(self, test):
        super(CompositeTestResult, self).addUnexpectedSuccess(test)
        self._call_delegates('addUnexpectedSuccess', test)
