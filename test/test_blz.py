import random
import unittest
import sys
import logging
import codecs
import blz.blzHelperInterface as blz


sys.path.insert(0, "..")
#from blz.blzHelperInterface import BlzHelperInterface as blz
from blz.fakeDomoticz import Parameters
from blz.fakeDomoticz import Devices

import configparser

# set up log
# init ROOT logger from my_logger.logger_init()
from test.logger import logger_init
from test.logger import logger_cleanUp
logger_init()  # init root logger
logger = logging.getLogger(__name__)  # module logger


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
        self.assertTrue(blz.contains(s, "test"))
        self.assertTrue(blz.containsTest(s))
        self.assertTrue(blz.containsDebug(s))
        logging.getLogger().info("# test with  NONE value as myString")
        n = None
        self.assertFalse(blz.contains(n, "test"))
        self.assertFalse(blz.containsTest(n))
        self.assertFalse(blz.containsDebug(n))
        logging.getLogger().info("# test NONE in search")
        n = None
        self.assertFalse(blz.contains(s, n))

        s:str = "Debug"
        self.assertFalse(blz.contains(s, "test"))
        self.assertFalse(blz.containsTest(s))
        self.assertTrue(blz.containsDebug(s))
