#!/usr/bin/env python

import os
from setuptools import setup, find_packages

# Load version information
xmlrunner_version = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'src', 'xmlrunner', 'version.py'
)
exec(compile(open(xmlrunner_version).read(), xmlrunner_version, 'exec'))


setup(
    name = 'unittest-xml-reporting',
    version = __version__,
    author = 'Daniel Fernandes Martins',
    author_email = 'daniel.tritone@gmail.com',
    description = 'PyUnit-based test runner with JUnit like XML reporting.',
    license = 'LGPL',
    platforms = ['Any'],
    keywords = ['pyunit', 'unittest', 'junit xml', 'report', 'testrunner'],
    url = 'http://github.com/danielfm/unittest-xml-reporting/tree/master/',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Testing'
    ],
    packages = find_packages('src'),
    package_dir = {'':'src'},
    zip_safe = False,
    include_package_data = True,
    test_suite = 'xmlrunner.tests.testsuite'
)
