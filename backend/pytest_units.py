"""
Unit tests
"""

from test.unit_tests.pytest_amazon_units import TestAmazonUnits
import unittest
from test.unit_tests.pytest_odoo_units import TestOdooUnits, TestOdooUnits2


def test_amazon_units():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAmazonUnits)
    unittest.TextTestRunner(verbosity=2).run(suite)

def test_odoo_units():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOdooUnits)
    # suite = unittest.TestLoader().loadTestsFromTestCase(TestOdooUnits2)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    test_amazon_units()
    # test_odoo_units()
