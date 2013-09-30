import random
import unittest
import sys

import xmlrunner


class TestSomething(unittest.TestCase):
    def test_invalid_xml_unicode(self):
        print(u'invalid xml: \x01\x0B\xfffe')


class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.seq = list(range(10))

    def test_shuffle(self):
        # make sure the shuffled sequence does not lose any elements
        random.shuffle(self.seq)
        self.seq.sort()
        self.assertEqual(self.seq, list(range(10)))

        # should raise an exception for an immutable sequence
        self.assertRaises(TypeError, random.shuffle, (1,2,3))

    def test_choice(self):
        print u"this is stdout\x01\x0B"
        print >> sys.stderr, u"this is stderr\x01\x0B"
        element = random.choice(self.seq)
        self.assertTrue(element in self.seq)

    @unittest.skip(u"some reason\x01\x0B")
    def test_skip(self):
        fail('Should not be called')

    def some_other_method(self):
        fail('Should not be called')

    @unittest.expectedFailure
    def test_unexpected_success(self):
        """Expected failure test""" # Override test name
        pass

    def test_error(self):
        raise RuntimeError(u"Error msg\x01\x0B")

    def test_sample(self):
        with self.assertRaises(ValueError):
            random.sample(self.seq, 20)

        for element in random.sample(self.seq, 5):
            self.assertTrue(element in self.seq)

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='test-reports'))
