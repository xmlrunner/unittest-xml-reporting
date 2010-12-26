# -*- coding: utf-8 -*-

"""Custom Django test runner that runs the tests using the
XMLTestRunner class.

This script shows how to use the XMLTestRunner in a Django project. To learn
how to configure a custom TestRunner in a Django project, please read the
Django docs website.
"""

from django.test.simple import *
import xmlrunner

class XMLTestRunner(DjangoTestSuiteRunner):
    def run_tests(self, test_labels, verbosity=1, interactive=True, extra_tests=[]):
        """
        Run the unit tests for all the test labels in the provided list.
        Labels must be of the form:
         - app.TestClass.test_method
            Run a single specific test method
         - app.TestClass
            Run all the test methods in a given class
         - app
            Search for doctests and unittests in the named application.

        When looking for tests, the test runner will look in the models and
        tests modules for the application.
        
        A list of 'extra' tests may also be provided; these tests
        will be added to the test suite.
        
        Returns the number of tests that failed.
        """
        setup_test_environment()
        
        settings.DEBUG = False
        
        verbose = getattr(settings, 'TEST_OUTPUT_VERBOSE', False)
        descriptions = getattr(settings, 'TEST_OUTPUT_DESCRIPTIONS', False)
        output = getattr(settings, 'TEST_OUTPUT_DIR', '.')
        
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

        old_config = self.setup_databases()

        result = xmlrunner.XMLTestRunner(
            verbose=verbose, descriptions=descriptions, output=output).run(suite)
        
        self.teardown_databases(old_config)
        teardown_test_environment()
        
        return len(result.failures) + len(result.errors)
