import random
import unittest
import sys
import logging
import codecs


sys.path.insert(0, "..")
import blz.blzHelperInterface
import configparser

# set up logger
logger = logging.getLogger()
logger.level = logging.DEBUG

class Test_blz(unittest.TestCase):
    def setUp(self):
        # work around logger
        self.stream_handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(self.stream_handler)
        logging.getLogger().info("# set up test for common blz utils")

    def tearDown(self):
        logging.getLogger().info("# tear down: test for blz")
        #if self.dwd:
        #    self.dwd.reset()
        #    self.dwd = None

        # remove logger
        logger.removeHandler(self.stream_handler)

    def test_Contains(self):
        s:str = "Test Debug"
        logging.getLogger().info("# test with  booth values given")
        self.assertTrue(blz.blzHelperInterface.contains(s, "test"))
        self.assertTrue(blz.blzHelperInterface.containsTest(s))
        self.assertTrue(blz.blzHelperInterface.containsDebug(s))
        logging.getLogger().info("# test with  NONE value as myString")
        n = None
        self.assertFalse(blz.blzHelperInterface.contains(n, "test"))
        self.assertFalse(blz.blzHelperInterface.containsTest(n))
        self.assertFalse(blz.blzHelperInterface.containsDebug(n))
        logging.getLogger().info("# test NONE in search")
        n = None
        self.assertFalse(blz.blzHelperInterface.contains(s, n))

        s:str = "Debug"
        self.assertFalse(blz.blzHelperInterface.contains(s, "test"))
        self.assertFalse(blz.blzHelperInterface.containsTest(s))
        self.assertTrue(blz.blzHelperInterface.containsDebug(s))
