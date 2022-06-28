from django.test import TestCase


# Create your tests here.
class DummyTestCase(TestCase):
    """Collection of dummy test cases"""

    def test_pass(self):
        """Test Pass"""
        pass

    def test_negative_comment1(self):
        """Use a close comment XML tag -->"""
        pass

    def test_negative_comment2(self):
        """Check XML tag </testsuites>"""
        pass
