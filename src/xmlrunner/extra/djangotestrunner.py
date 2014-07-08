# -*- coding: utf-8 -*-

"""
Custom Django test runner that runs the tests using the
XMLTestRunner class.

This script shows how to use the XMLTestRunner in a Django project. To learn
how to configure a custom TestRunner in a Django project, please read the
Django docs website.
"""

from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner
import xmlrunner

# if using django-discover-runner, pretty much the same thing
# class XMLDiscoverTestRunner(discover_runner.DiscoverRunner):
class XMLTestRunner(DjangoTestSuiteRunner):

    def run_suite(self, suite, **kwargs):
        verbosity = getattr(settings, 'TEST_OUTPUT_VERBOSE', 1)
        #XXX: verbosity = self.verbosity
        if isinstance(verbosity, bool):
            verbosity = (1, 2)[verbosity]
        descriptions = getattr(settings, 'TEST_OUTPUT_DESCRIPTIONS', False)
        output = getattr(settings, 'TEST_OUTPUT_DIR', '.')
        return xmlrunner.XMLTestRunner(
            verbosity=verbosity, descriptions=descriptions,
            output=output, failfast=self.failfast).run(suite)

