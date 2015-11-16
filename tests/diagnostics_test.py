from six import StringIO
from tempfile import mkdtemp

from xmlrunner.unittest import unittest

try:
    import diagnostics
except ImportError:
    diagnostics = None

class DiagnosticsTest(unittest.TestCase):
    class DummyTest(unittest.TestCase):
        # We should reuse code from testsuite.py in future.
        def test_fail(self):
            self.assertTrue(False)

    def setUp(self):
        self.stream = StringIO()
        self.outdir = mkdtemp()

    @unittest.skipIf(diagnostics is None, 'diagnostics not found')
    def test_diagnostics_runner(self):
        from xmlrunner.extra.diagnosticstestrunner import DiagnosticsTestInfo, XMLTestRunner
        suite = unittest.TestSuite()
        suite.addTest(self.DummyTest('test_fail'))
        runner = XMLTestRunner(stream=self.stream, output=self.outdir)
        self.assertEquals(runner.info_cls, DiagnosticsTestInfo)
        result = runner.run(suite)
        self.assertEqual(len(result.failures), 1)
        failure_obj = result.failures[0][0]
        self.assertTrue(isinstance(failure_obj, DiagnosticsTestInfo))
        failure_attrs = failure_obj.get_failure_attributes()
        self.assertIn("details", failure_attrs.keys())
