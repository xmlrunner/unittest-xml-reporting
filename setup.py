from setuptools import setup

from xmlrunner import get_version

setup(
    name = 'unittest-xml-reporting',
    version = get_version(),
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
    test_suite = 'tests.testsuite',
    tests_require = ['mock']
)
