unittest-xml-reporting
======================

``unittest-xml-reporting`` is a ``unittest`` test runner that can save
test results to XML files (jUnit) and be consumed by a wide range of
tools such as continuous integration systems.


Getting started
===============

Similar to the ``unittest`` module, you can run::

    python -m xmlrunner test_module
    python -m xmlrunner module.TestClass
    python -m xmlrunner module.Class.test_method

as well as::

    python -m xmlrunner discover [options]

You can also add a top level file to allow running the tests with
the command ``python tests.py``, and configure the test runner
to output the XML reports in the ``test-reports`` directory. ::

    # tests.py

    if __name__ == '__main__':
        unittest.main(
            testRunner=xmlrunner.XMLTestRunner(output='test-reports'),
            # these make sure that some options that are not applicable
            # remain hidden from the help menu.
            failfast=False, buffer=False, catchbreak=False)



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

