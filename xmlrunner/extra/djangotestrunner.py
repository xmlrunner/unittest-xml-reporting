# -*- coding: utf-8 -*-

"""
Custom Django test runner that runs the tests using the
XMLTestRunner class.

This script shows how to use the XMLTestRunner in a Django project. To learn
how to configure a custom TestRunner in a Django project, please read the
Django docs website.
"""

import django
from django.conf import settings

# future compatibilty with django
# in django 1.6 DiscoverRunner bacame default and
# DjangoTestSuiteRunner became depecated, will be removed in 1.8
if django.VERSION < (1, 6):
    from django.test.simple import DjangoTestSuiteRunner
    _DjangoRunner = DjangoTestSuiteRunner
else:
    from django.test.runner import DiscoverRunner
    _DjangoRunner = DiscoverRunner

import xmlrunner

class XMLTestRunner(_DjangoRunner):

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

