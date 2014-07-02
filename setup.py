
import os
import sys
from setuptools import setup, find_packages
from distutils.util import convert_path

main_ns = {}
ver_path = convert_path('xmlrunner/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

install_requires, setup_requires, tests_require = ['six'], ['six'], ['six','mock']

import sys
if sys.version_info < (2, 7):
    install_requires += ['unittest2']
    setup_requires += ['unittest2']
    tests_require += ['unittest2']

setup(
    name = 'unittest-xml-reporting',
    version = main_ns['__version__'],
    author = 'Daniel Fernandes Martins',
    author_email = 'daniel.tritone@gmail.com',
    description = 'unittest-based test runner with Ant/JUnit like XML reporting.',
    license = 'BSD',
    platforms = ['Any'],
    keywords = ['pyunit', 'unittest', 'ant', 'junit', 'xml', 'report', 'testrunner'],
    url = 'https://github.com/danielfm/unittest-xml-reporting/',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Testing'
    ],
    packages = find_packages(),
    install_requires = install_requires,
    setup_requires = setup_requires,
    test_suite = 'tests.testsuite',
    tests_require = tests_require
)
