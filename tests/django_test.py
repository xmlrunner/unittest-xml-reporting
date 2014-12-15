
from xmlrunner.unittest import unittest

import sys
import os
from os import path, chdir, getcwd

try:
    import django
except ImportError:
    django = None

TESTS_DIR = path.dirname(__file__)

class DjangoTest(unittest.TestCase):
    def setUp(self):
        self._old_cwd = getcwd()
        self.project_dir = path.abspath(path.join(TESTS_DIR, 'django_example'))
        chdir(self.project_dir)
        sys.path.append(self.project_dir)
        import django.conf
        django.conf.settings = django.conf.LazySettings()
        # os.environ['DJANGO_SETTINGS_MODULE'] = 'django_example.settings'

    def tearDown(self):
        chdir(self._old_cwd)
        # del os.environ['DJANGO_SETTINGS_MODULE']

    def _check_runner(self, runner):
        suite = runner.build_suite(test_labels=['app2','app'])
        test_ids = [ test.id() for test in suite ]
        self.assertEqual(test_ids, [
            'app2.tests.DummyTestCase.test_pass',
            'app.tests.DummyTestCase.test_pass',
        ])
        suite = runner.build_suite(test_labels=[])
        test_ids = [ test.id() for test in suite ]
        self.assertEqual(test_ids, [
            'app.tests.DummyTestCase.test_pass',
            'app2.tests.DummyTestCase.test_pass',
        ])

    @unittest.skipIf(django is None, 'django not found')
    def test_django_runner(self):
        from django.conf import settings
        settings.configure(INSTALLED_APPS=['app','app2'])
        from django.test.utils import get_runner
        runner_class = get_runner(settings)
        runner = runner_class()
        self._check_runner(runner)

    @unittest.skipIf(django is None, 'django not found')
    def test_django_xmlrunner(self):
        from django.conf import settings
        settings.configure(
            TEST_RUNNER='xmlrunner.extra.djangotestrunner.XMLTestRunner')
        from django.test.utils import get_runner
        runner_class = get_runner(settings)
        runner = runner_class()
        self._check_runner(runner)
