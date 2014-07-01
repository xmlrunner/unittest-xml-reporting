
__all__ = ('XMLTestRunner',)

import sys
import unittest
from xmlrunner import composite, result

class XMLTestRunner(unittest.TextTestRunner):
    """Subclass of `TextTestRunner` which was modified so it uses a
    `CompositeTestResult` with both `TextTestResult` and `XMLTestResult` as
    delegates.
    """

    def __init__(self, output='.', outsuffix=None, stream=sys.stderr,
            descriptions=True, verbosity=1, failfast=False, buffer=False):
        """Creates a new instance.
        """
        super(XMLTestRunner, self).__init__(stream=stream, descriptions=descriptions,
            verbosity=verbosity, failfast=failfast, buffer=buffer)

        self.output = output
        self.out_suffix = outsuffix

    def _makeResult(self):
        """Returns an instance of `CompositeTestResult` capable of rendering
        the results in both text and XML formats.
        """
        xml_result = result.XMLTestResult(self.stream, self.descriptions,
            self.verbosity, self.output, self.out_suffix)

        text_result = super(XMLTestRunner, self)._makeResult()
        return composite.CompositeTestResult(text_result, [xml_result])
