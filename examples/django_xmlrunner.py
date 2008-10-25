# -*- coding: utf-8 -*-

"""Custom Django test runner that runs the tests using the
XMLTestRunner class.
"""

from django.test.simple import *
import xmlrunner


def default_settings(module, attr, default_value):
    "Sets a value to the settings if it can't be found."
    if not hasattr(module, attr):
        setattr(module, attr, default_value)

def run_tests(test_labels, verbosity=1, interactive=True, extra_tests=[]):
    "Run the tests."
    setup_test_environment()
    
    settings.DEBUG = False
    default_settings(settings, 'TEST_OUTPUT_VERBOSE', False)
    default_settings(settings, 'TEST_OUTPUT_DESCRIPTIONS', False)
    default_settings(settings, 'TEST_OUTPUT_DIR', '.')
    suite = unittest.TestSuite()
    
    if test_labels:
        for label in test_labels:
            if '.' in label:
                suite.addTest(build_test(label))
            else:
                app = get_app(label)
                suite.addTest(build_suite(app))
    else:
        for app in get_apps():
            suite.addTest(build_suite(app))
    
    for test in extra_tests:
        suite.addTest(test)
    
    old_name = settings.DATABASE_NAME
    from django.db import connection
    connection.creation.create_test_db(verbosity, autoclobber=not interactive)
    
    result = xmlrunner.XMLTestRunner(
        verbose=settings.TEST_OUTPUT_VERBOSE, \
        descriptions=settings.TEST_OUTPUT_DESCRIPTIONS, \
        output=settings.TEST_OUTPUT_DIR).run(suite)
    
    connection.creation.destroy_test_db(old_name, verbosity)
    teardown_test_environment()
    return len(result.failures) + len(result.errors)
