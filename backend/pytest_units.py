"""
Unit tests
"""

from test.unit_tests.pytest_amazon_units import TestAmazonUnits
import unittest

def testAmazonUnits():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAmazonUnits)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    testAmazonUnits()
