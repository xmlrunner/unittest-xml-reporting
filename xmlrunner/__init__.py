
__all__ = ('XMLTestRunner',)

import sys
if sys.version_info < (2, 7):
    # monkey patch unittest
    import unittest2 as unittest
    sys.modules['unittest'] = sys.modules['unittest2']
    import unittest.result
    class _TestResult(unittest.result.TestResult):
        def __init__(self, stream=None, descriptions=None, verbosity=None):
            super(_TestResult, self).__init__()
    setattr(unittest.result, 'TestResult', _TestResult)
    setattr(unittest, 'TestResult', _TestResult)

import xmlrunner.version
from xmlrunner.runner import XMLTestRunner

__version__ = xmlrunner.version.__version__
