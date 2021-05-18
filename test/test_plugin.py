from blz.fakeDomoticz import Parameters
import unittest
import sys
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

# set up logger
logger = logging.getLogger()
logger.level = logging.DEBUG


class Test_plugin(unittest.TestCase):
    def setUp(self):
        # work around logger
        self.stream_handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(self.stream_handler)
        logging.getLogger().info("# set up test for dwd")
        self.plugin = BasePlugin() #plugin()

        config = configparser.ConfigParser()
        config.read_file(codecs.open(r"./test/my_config.ini", encoding="utf-8"))
        self.dwd = self.readAndCreate(config, CONFIG_SECTION_MY)

        self.plugin.dwd = self.dwd

    def tearDown(self):
        logging.getLogger().info("# tear down: test for dwd")
        if self.plugin:
            self.plugin = None

        # remove logger
        logger.removeHandler(self.stream_handler)

    def test_A_onStart(self):
        logging.getLogger().info("#fake start of plugin")
        #TODO call:
        self.plugin.onStart()

    def test_B_onHeartbeat(self):
        logging.getLogger().info("#fake heart beat")
        #TODO call:
        self.plugin.onStart()
        self.plugin.onHeartbeat()

    def test_C_onStop(self):
        logging.getLogger().info("#fake stop")
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
