from blz.fakeDomoticz import Parameters
import unittest
import sys
import os.path
import logging
import codecs

sys.path.insert(0, "..")
from blz.blzHelperInterface import BlzHelperInterface
from plugin import BasePlugin

from dwd.dwd import Dwd, RegionType
import configparser

CONFIG_SECTION_MY = "dwd_my"
CONFIG_SECTION_GEMEINDE_OBERSTDORF = "dwd_Gemeinde_Oberstdorf"
CONFIG_SECTION_KREIS_OBERALLGAEU = "dwd_Kreis_Oberallgaeu"

CONFIG_SECTION_KREIS_OBERHAVEL = "dwd_Kreis_Oberhavel"

CONFIG_SECTION_STADT_GREIZ = "dwd_Stadt_Greiz"
CONFIG_SECTION_BUGGY = "dwd_buggy"

# set up log
# init ROOT logger from my_logger.logger_init()
from test.logger import logger_init
from test.logger import logger_cleanUp
logger_init()  # init root logger
logger = logging.getLogger(__name__)  # module logger


class Test_plugin(unittest.TestCase):
    def setUp(self):
        # work around logger
        logger.info("# set up test for dwd")
        self.plugin = BasePlugin() #plugin()

        config = configparser.ConfigParser()
        conf = r"./test/my_config.ini"
        logger.info("search personal conf")
        if os.path.isfile(conf):
            logger.info("found personal conf")
            config.read_file(codecs.open(conf, encoding="utf-8"))
            self.dwd = self.readAndCreate(config, CONFIG_SECTION_MY)
        else:
            logger.warn("did not found my_config using common.")
            conf = r"./test/common_config.ini"
            config.read_file(codecs.open(conf, encoding="utf-8"))
            self.dwd = self.readAndCreate(config, CONFIG_SECTION_GEMEINDE_OBERSTDORF)
        self.plugin.dwd = self.dwd

    def tearDown(self):
        logger.info("# tear down: test for dwd")
        if self.plugin:
            self.plugin = None

        # remove logger
        logger_cleanUp()

    def test_A_onStart(self):
        logger.info("#fake start of plugin")
        #TODO call:
        self.plugin.onStart()

    def test_A_onStart_Missing_Conf(self):
        logger.error("please insert test")
        #TODO call:
        #self.plugin.onStart()

    def test_B_onHeartbeat(self):
        logger.info("#fake heart beat")
        #TODO call:
        self.plugin.onStart()
        self.plugin.onHeartbeat()

    def test_C_onStop(self):
        logger.info("#fake stop")
        #TODO call:
        self.plugin.onStop()

    def readAndCreate(self, aConfig, aSection):
        """creates a dwd object based on config

        Args:
            aConfig ([type]): [configuration holding the settings]

        Returns:
            [dwd]: [dwd object]
        """
        self.assertTrue(
            aConfig.has_section(aSection),
            "we need this set up:  " + aSection,
        )
        cellId = aConfig.get(aSection, "cellId")
        region = aConfig.get(aSection, "region")
        Parameters['Mode1'] = cellId
        Parameters['Mode2'] = region
        Parameters['Mode3'] = "event"
        rT: RegionType = RegionType.getByName(region)
        aDwd = Dwd(dwdWarnCellId=cellId, regionType=rT)

        return aDwd


if "__main__" == __name__:
    unittest.main()
