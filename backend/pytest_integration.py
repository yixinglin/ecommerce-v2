"""
Integration tests
"""

from test.integration_tests.pytest_present_amazon import (TestAmazonIntegration,
                                                          TestAmazonPickPackService,
                                                          )
import unittest

def test_amazon_integration():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAmazonIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

def test_amazon_pickpack_service():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAmazonPickPackService)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == '__main__':
    test_amazon_integration()
    test_amazon_pickpack_service()
