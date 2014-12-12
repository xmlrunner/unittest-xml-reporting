
from __future__ import absolute_import

import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
    from unittest2.runner import TextTestRunner
    from unittest2.runner import TextTestResult as _TextTestResult
    from unittest2.result import TestResult
    from unittest2.main import TestProgram
else:
    import unittest
    from unittest import TextTestRunner
    from unittest import TestResult, _TextTestResult
    from unittest.main import TestProgram
    try:
        from unittest.main import USAGE_AS_MAIN
        TestProgram.USAGE = USAGE_AS_MAIN
    except ImportError:
        pass
