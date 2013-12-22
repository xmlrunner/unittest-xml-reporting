#!/usr/bin/env python

import os
from setuptools import setup, find_packages

# Load version information
xmlrunner_version = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'xmlrunner', 'version.py'
)
exec(compile(open(xmlrunner_version).read(), xmlrunner_version, 'exec'))


setup(
    name = 'xmlrunner',
    py_modules=['xmlrunner'],
    version = __version__,
    author = 'Daniel Fernandes Martins',
    author_email = 'daniel.tritone@gmail.com',
    description = 'PyUnit-based test runner with JUnit like XML reporting.',
    license = 'LGPL',
    platforms = ['Any'],
    keywords = ['pyunit', 'unittest', 'junit xml', 'report', 'testrunner'],
    url = 'https://github.com/pycontribs/xmlrunner',
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
    packages = ['xmlrunner'],
    provides = ['xmlrunner'],
    zip_safe = True,
    include_package_data = True,
    test_suite = 'xmlrunner.tests.test_xmlrunner'
)
