# -*- coding: utf-8

import runpy
import sys
from unittest import mock
from unittest.mock import patch

from xmlrunner.runner import XMLTestRunner
from xmlrunner.unittest import unittest


class MainTest(unittest.TestCase):
    """Tests __main__.py module."""

    def test_xmloutput_param_none(self):
        self._test_xmloutput_param('.')

    def test_xmloutput_param_set(self):
        output = 'test-results'
        testargs = list(sys.argv)
        testargs.extend(('--xmloutput', output))
        with patch.object(sys, 'argv', testargs):
            self._test_xmloutput_param(output)

    @mock.patch.object(XMLTestRunner, '__init__', mock.Mock(return_value=None))
    @mock.patch.object(unittest.TestProgram, '__init__', mock.Mock(return_value=None))
    def _test_xmloutput_param(self, output):
        runpy.run_module('xmlrunner.__main__')
        self.assertTrue(XMLTestRunner.__init__.called_with(output=output))
