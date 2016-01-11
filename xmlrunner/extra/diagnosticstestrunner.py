"""Integration with diagnostics module.

Custom test runner that uses diagnostics module to generate
pretty tracebacks in html format and adds links to generated html
files into resulted xml report (every "error" tag now has "details"
attribute).

Usage:

import unittest
from xmlrunner.extra.diagnosticstestrunner import XMLTestRunner

class MyTestCase(unittest.TestCase):
    def test_mytest(self):
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main(testRunner=XMLTestRunner())
"""

from diagnostics import exception_hook, FileStorage, ExceptionInfo

from xmlrunner.result import _TestInfo
from xmlrunner.runner import XMLTestRunner as _XMLTestRunner


class DiagnosticsTestInfo(_TestInfo):

    def __init__(self, test_result, test_method, outcome=_TestInfo.SUCCESS,
                 err=None, subTest=None):
        super(DiagnosticsTestInfo, self).__init__(
            test_result, test_method, outcome=outcome, err=err, subTest=subTest)
        self._details_path = self._exception_details_path(err)
        if err:
            exception_hook(*err)

    def _exception_details_path(self, err):
        """Return file name with details about exception err"""
        if isinstance(err, basestring) or err is None:
            return ""
        return exception_hook.storage._build_path_to_file(ExceptionInfo(err))

    def get_failure_attributes(self, *args, **kwargs):
        res = super(DiagnosticsTestInfo, self).get_failure_attributes(*args, **kwargs)
        res["details"] = self._details_path
        return res


class XMLTestRunner(_XMLTestRunner):
    def __init__(self, *args, **kwargs):
        directory = kwargs.get("output", ".")
        exception_hook.enable(FileStorage(directory))
        kwargs["info_cls"] = DiagnosticsTestInfo
        super(XMLTestRunner, self).__init__(*args, **kwargs)
