from unittest import skipIf

from django.test import TestCase


# Create your tests here.
@skipIf(condition=True, reason=True)
class SkipTestCase(TestCase):
    def test_skip(self):
        """Test Skip"""
        pass

