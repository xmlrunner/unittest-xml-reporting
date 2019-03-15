[![License](https://img.shields.io/pypi/l/unittest-xml-reporting.svg)](https://pypi.python.org/pypi/unittest-xml-reporting/)
[![Latest Version](https://img.shields.io/pypi/v/unittest-xml-reporting.svg)](https://pypi.python.org/pypi/unittest-xml-reporting/)
[![Development Status](https://img.shields.io/pypi/status/unittest-xml-reporting.svg)](https://pypi.python.org/pypi/unittest-xml-reporting/)
[![Documentation Status](https://readthedocs.org/projects/unittest-xml-reporting/badge/?version=latest)](http://unittest-xml-reporting.readthedocs.io/en/latest/?badge=latest)

[![Build Status](https://travis-ci.org/xmlrunner/unittest-xml-reporting.svg?branch=master)](https://travis-ci.org/xmlrunner/unittest-xml-reporting)
[![Code Health](https://landscape.io/github/xmlrunner/unittest-xml-reporting/master/landscape.svg?style=flat)](https://landscape.io/github/xmlrunner/unittest-xml-reporting/master)
[![codecov.io Coverage Status](https://codecov.io/github/xmlrunner/unittest-xml-reporting/coverage.svg?branch=master)](https://codecov.io/github/xmlrunner/unittest-xml-reporting?branch=master)
[![Coveralls Coverage Status](https://coveralls.io/repos/xmlrunner/unittest-xml-reporting/badge.svg?branch=master&service=github)](https://coveralls.io/github/xmlrunner/unittest-xml-reporting?branch=master)
[![Requirements Status](https://requires.io/github/xmlrunner/unittest-xml-reporting/requirements.svg?branch=master)](https://requires.io/github/xmlrunner/unittest-xml-reporting/requirements/?branch=master)

# unittest-xml-reporting (aka xmlrunner)

A unittest test runner that can save test results to XML files in xUnit format.
The files can be consumed by a wide range of tools, such as build systems, IDEs
and continuous integration servers.

## Schema

There are many schemas with minor differences.
We use one that is compatible with Jenkins xUnit plugin, a copy is
available under `tests/vendor/jenkins/xunit-plugin/junit-10.xsd` (see attached license).
You may also find these resources useful:

- https://stackoverflow.com/questions/4922867/what-is-the-junit-xml-format-specification-that-hudson-supports
- https://stackoverflow.com/questions/11241781/python-unittests-in-jenkins
- [Jenkins (junit-10.xsd)](https://github.com/jenkinsci/xunit-plugin/blob/master/src/main/resources/org/jenkinsci/plugins/xunit/types/model/xsd/junit-10.xsd)
- [JUnit-Schema (JUnit.xsd)](https://github.com/windyroad/JUnit-Schema/blob/master/JUnit.xsd)
- [Windyroad (JUnit.xsd)](http://windyroad.com.au/dl/Open%20Source/JUnit.xsd)
- [a gist (Jenkins xUnit test result schema)](https://gist.github.com/erikd/4192748)

## Things that are somewhat broken

Python 3 has the concept of sub-tests for a `unittest.TestCase`; this doesn't map well to an existing
xUnit concept, so you won't find it in the schema. What that means, is that you lose some granularity
in the reports for sub-tests.

## Requirements

* Python 2.7 or 3.3+
* Please note Python 2.6 end-of-life was in Oct 2013, last version supporting 2.6 was 1.14.0

## Installation

The easiest way to install unittest-xml-reporting is via
[Pip](http://www.pip-installer.org):

````bash
$ pip install unittest-xml-reporting
````

If you use Git and want to get the latest *development* version:

````bash
$ git clone https://github.com/xmlrunner/unittest-xml-reporting.git
$ cd unittest-xml-reporting
$ sudo python setup.py install
````

Or get the latest *development* version as a tarball:

````bash
$ wget https://github.com/xmlrunner/unittest-xml-reporting/archive/master.zip
$ unzip master.zip
$ cd unittest-xml-reporting
$ sudo python setup.py install
````

Or you can manually download the latest released version from
[PyPI](https://pypi.python.org/pypi/unittest-xml-reporting/).


## Command-line

````bash
python -m xmlrunner [options]
python -m xmlrunner discover [options]

# help
python -m xmlrunner -h
````

e.g. 
````bash
python -m xmlrunner discover -t ~/mycode/tests -o /tmp/build/junit-reports
````

## Usage

The script below, adapted from the
[unittest](http://docs.python.org/library/unittest.html), shows how to use
`XMLTestRunner` in a very simple way. In fact, the only difference between
this script and the original one is the last line:

````python
import random
import unittest
import xmlrunner

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.seq = list(range(10))

    @unittest.skip("demonstrating skipping")
    def test_skipped(self):
        self.fail("shouldn't happen")

    def test_shuffle(self):
        # make sure the shuffled sequence does not lose any elements
        random.shuffle(self.seq)
        self.seq.sort()
        self.assertEqual(self.seq, list(range(10)))

        # should raise an exception for an immutable sequence
        self.assertRaises(TypeError, random.shuffle, (1,2,3))

    def test_choice(self):
        element = random.choice(self.seq)
        self.assertTrue(element in self.seq)

    def test_sample(self):
        with self.assertRaises(ValueError):
            random.sample(self.seq, 20)
        for element in random.sample(self.seq, 5):
            self.assertTrue(element in self.seq)

if __name__ == '__main__':
    unittest.main(
        testRunner=xmlrunner.XMLTestRunner(output='test-reports'),
        # these make sure that some options that are not applicable
        # remain hidden from the help menu.
        failfast=False, buffer=False, catchbreak=False)
````

### Reporting to a single file

````python
if __name__ == '__main__':
    with open('/path/to/results.xml', 'wb') as output:
        unittest.main(
            testRunner=xmlrunner.XMLTestRunner(output=output),
            failfast=False, buffer=False, catchbreak=False)
````

### Doctest support

The XMLTestRunner can also be used to report on docstrings style tests.

````python
import doctest
import xmlrunner

def twice(n):
    """
    >>> twice(5)
    10
    """
    return 2 * n

class Multiplicator(object):
    def threetimes(self, n):
        """
        >>> Multiplicator().threetimes(5)
        15
        """
        return 3 * n

if __name__ == "__main__":
    suite = doctest.DocTestSuite()
    xmlrunner.XMLTestRunner().run(suite)
````

### Django support

In order to plug `XMLTestRunner` to a Django project, add the following
to your `settings.py`:

````python
TEST_RUNNER = 'xmlrunner.extra.djangotestrunner.XMLTestRunner'
````

Also, the following settings are provided so you can fine tune the reports:

|setting|default|values|description|
|-|-|-|-|
|`TEST_OUTPUT_VERBOSE`|`1`|`0\|1\|2`|Besides the XML reports generated by the test runner, a bunch of useful information is printed to the `sys.stderr` stream, just like the `TextTestRunner` does. Use this setting to choose between a verbose and a non-verbose output.|
|`TEST_OUTPUT_DESCRIPTIONS`|`False`|`True\|False`|If your test methods contains docstrings, you can display such docstrings instead of display the test name (ex: `module.TestCase.test_method`).<br>In order to use this feature, you have to enable verbose output by setting `TEST_OUTPUT_VERBOSE = 2`.<br>Only effects stdout and not XML output.|
|`TEST_OUTPUT_DIR`|`"."`|`<str>`|Tells the test runner where to put the XML reports. If the directory couldn't be found, the test runner will try to create it before generate the XML files.|
|`TEST_OUTPUT_FILE_NAME`|`None`|`<str>`|Tells the test runner to output a single XML report with this filename under `os.path.join(TEST_OUTPUT_DIR, TEST_OUTPUT_FILE_NAME)`.<br>Please note that for long running tests, this will keep the results in memory for a longer time than multiple reports, and may use up more resources.|


## Contributing

We are always looking for good contributions, so please just fork the
repository and send pull requests (with tests!).

If you would like write access to the repository, or become a maintainer,
feel free to get in touch.


### Testing changes with `tox`

Please use `tox` to test your changes before sending a pull request.
You can find more information about `tox` at <https://testrun.org/tox/latest/>.

```bash
$ pip install tox

# basic sanity test, friendly output
$ tox -e pytest

# all combinations
$ tox
```

## Work in progress

There is a [rewrite branch](https://github.com/xmlrunner/unittest-xml-reporting/tree/rewrite) which contains better unit tests and uses a different runner. It
introduces a `CompositeTestResult` which allows the use of both `TextTestResult`
and `XMLTestResult` as delegates. If you would like to help reconcile both
branches, pull requests are welcome.
