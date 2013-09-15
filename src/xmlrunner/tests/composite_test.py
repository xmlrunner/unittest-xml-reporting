from mock import patch, Mock

import unittest

from xmlrunner.composite import CompositeTestResult

class _DumbTestResult(unittest.TestResult):
    """Empty TestResult subclass for testing purposes.
    """

    def __init__(self, *args, **kwargs):
        super(_DumbTestResult, self).__init__(*args, **kwargs)


class CompositeTestResultTest(unittest.TestCase):
    """CompositeTestResult test cases.
    """

    def setUp(self):
        """Creates a CompositeTestResult composed of a TextTestResult and a
        _DumbTestResult."""

        self.delegate = unittest.TextTestResult(stream='used', verbosity=0,
            descriptions=False)
        self.extra = _DumbTestResult(stream='unused')
        self.result = CompositeTestResult(self.delegate, [self.extra])

    @patch.object(unittest.TextTestResult, 'startTest')
    def test_proxy_call_to_delegate_result(self, mock):
        """CompositeTestResult should forward calls to methods public defined in
        TestResult to the main delegate.
        """
        self.result.startTest('arg')
        mock.assert_called_with('arg')

    @patch.object(_DumbTestResult, 'startTest')
    def test_proxy_call_to_extra_result(self, mock):
        """CompositeTestResult should forward calls to methods public defined in
        TestResult to the extra delegates.
        """
        self.result.startTest('arg')
        mock.assert_called_with('arg')

    def test_delegate_getattr(self):
        """Access of unknown attributes must be forwarded to the main delegate.
        """
        self.assertEqual(self.result.stream, 'used')
