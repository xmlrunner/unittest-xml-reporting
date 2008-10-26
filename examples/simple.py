# -*- coding: utf-8 -*-

"""A simple test script that shows how to use the XMLTestRunner with plain
Python modules.
"""

import random
import unittest
import xmlrunner

class TestSequenceFunctions(unittest.TestCase):
    
    def setUp(self):
        self.seq = range(10)

    def test_shuffle(self):
        # make sure the shuffled sequence does not lose any elements
        random.shuffle(self.seq)
        self.seq.sort()
        self.assertEqual(self.seq, range(10))

    def test_choice(self):
        element = random.choice(self.seq)
        self.assert_(element in self.seq)

    def test_sample(self):
        self.assertRaises(ValueError, random.sample, self.seq, 20)
        for element in random.sample(self.seq, 5):
            self.assert_(element in self.seq)

    def test_some_failure(self):
        print 'Writing a string to the standard output'
        self.assertFalse(True, 'False should be false, I think')

    def test_some_error(self):
        None + 100

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSequenceFunctions)
    xmlrunner.XMLTestRunner(output='test-reports').run(suite)
