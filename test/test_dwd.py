import random
import unittest
import sys
import logging
import codecs
from dwd.dwd import (
    Dwd,
    DwdAlertColor,
    DwdDetailLevel,
    DwdIcons,
    Severity,
    RegionType,
    RegionTypeCommon,
    RegionTypeWarning,
)
import configparser

sys.path.insert(0, "..")
CONFIG_SECTION_MY = "dwd_my"
CONFIG_SECTION_GEMEINDE_OBERSTDORF = "dwd_Gemeinde_Oberstdorf"
CONFIG_SECTION_KREIS_OBERALLGAEU = "dwd_Kreis_Oberallgaeu"

CONFIG_SECTION_KREIS_OBERHAVEL = "dwd_Kreis_Oberhavel"

CONFIG_SECTION_STADT_GREIZ = "dwd_Stadt_Greiz"

CONFIG_SECTION_STADT_HAMBURG = "dwd_Stadt_Hamburg"
CONFIG_SECTION_STADT_BERLIN = "dwd_Stadt_Berlin"

CONFIG_SECTION_STADT_FRANKFURT = "dwd_Stadt_Frankfurt"
CONFIG_SECTION_STADT_FRANKFURT2 = "dwd_Stadt_Frankfurt2"
CONFIG_SECTION_STADT_FRANKFURT_NORD = "dwd_Stadt_FrankfurtNord"
CONFIG_SECTION_STADT_FRANKFURT_SUED = "dwd_Stadt_FrankfurtSued"

CONFIG_SECTION_BUGGY = "dwd_buggy"

# set up logger
logger = logging.getLogger()
logger.level = logging.DEBUG


class Test_dwd(unittest.TestCase):
    def setUp(self):
        # work around logger
        self.stream_handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(self.stream_handler)
        logging.getLogger().info("# set up test for dwd")

    def tearDown(self):
        logging.getLogger().info("# tear down: test for dwd")
        # if self.dwd:
        #    self.dwd.reset()
        #    self.dwd = None

        # remove logger
        logger.removeHandler(self.stream_handler)

    def test_Enums(self):
        m = Severity.__members__
        self.assertIsNotNone(m)
        minor = Severity.getByName("Minor")
        self.assertIsNotNone(minor)

        srv = Severity.getByName("Severe")
        self.assertIsNotNone(srv)

        maxS = Severity.max(minor, srv)
        self.assertEquals(maxS, srv)

        maxS = Severity.max(srv, minor)
        self.assertEquals(maxS, srv)

        maxS = Severity.max(srv, None)
        self.assertEquals(maxS, srv)

        maxS = Severity.max(None, srv)
        self.assertEquals(maxS, srv)

        m = RegionTypeCommon.__members__
        self.assertIsNotNone(m)
        rC = RegionTypeCommon.KREIS
        self.assertIsNotNone(rC)

        m = RegionTypeWarning.__members__
        self.assertIsNotNone(m)
        rW = RegionTypeWarning.KREIS
        self.assertIsNotNone(rW)

        m = RegionType.__members__
        self.assertIsNotNone(m)
        rt = RegionType.KREIS
        self.assertIsNotNone(rt)
        rt2 = RegionType.getByName("Kreis")
        self.assertIsNotNone(rt2)
        self.assertEquals(rt, rt2)

        cl = DwdAlertColor.getBySeverity(random.choice(list(Severity)))
        self.assertIsNotNone(cl)

    def test_EnumIcon(self):
        c = DwdIcons.RAIN
        self.assertIsNotNone(c)
        s = c.getUrl
        self.assertIsNotNone(s)
        logging.getLogger().info("icon:{}\t url is:{}".format(c.name, s))
        icn = random.choice(list(DwdIcons))
        self.assertIsNotNone(icn)

    def test_EnumDetail(self):
        c = DwdDetailLevel.EVENT
        self.assertIsNotNone(c)

        logging.getLogger().info(
            "details:{}\tdetails:{}\ticon:{} ".format(c.name, c.showDetails, c.showIcon)
        )
        c2 = DwdDetailLevel.getByName("event")
        self.assertEquals(c, c2)

        n = DwdDetailLevel.getByName("")
        self.assertIsNone(n)

        n = DwdDetailLevel.getByName(" ")
        self.assertIsNone(n)

    def test_EnumColor(self):
        c = DwdAlertColor.DARK_RED
        self.assertIsNotNone(c)
        # l = c.severity
        h = c.hexColor
        self.assertIsNotNone(c)
        self.assertIsNotNone(h)
        sH = c.getColorAsHexString()
        self.assertIsNotNone(sH)
        logging.getLogger().info("color:{}\t colorHex is:{}".format(c.name, sH))
        self.assertEquals("#880e4f", sH)

        sR = c.getColorAsRGBString()
        logging.getLogger().info("color:{}\t colorRGB is:{}".format(c.name, sR))
        self.assertEquals("rgb(136, 14, 79)", sR)

        c2 = DwdAlertColor.getBySeverity(Severity.Extreme)
        self.assertIsNotNone(c2)
        self.assertEquals(c, c2)

    def test_myDwd(self):
        """
        takes address from **my** config and tests it
        """
        config = configparser.ConfigParser()
        config.read_file(codecs.open(r"./test/my_config.ini", encoding="utf-8"))

        self.dwd = self.readAndCreate(config, CONFIG_SECTION_MY)
        self.doWork(self.dwd)
        self.assertIsNotNone(self.dwd.getAlarmLevel)
        self.assertIsNotNone(self.dwd.getAlarmText)

    def test_Gemeinde_Oberstdorf(self):
        """
        takes standrad warncell from common config and tests it
        """

        config = configparser.ConfigParser()
        config.read_file(codecs.open(r"./test/common_config.ini", encoding="utf-8"))
        self.dwd = self.readAndCreate(aConfig=config, aSection=CONFIG_SECTION_GEMEINDE_OBERSTDORF)
        self.doWork(self.dwd)

    def test_Kreis_Oberallgaeu(self):
        """
        takes standrad warncell from common config and tests it
        """

        config = configparser.ConfigParser()
        config.read_file(codecs.open(r"./test/common_config.ini", encoding="utf-8"))
        self.dwd = self.readAndCreate(aConfig=config, aSection=CONFIG_SECTION_KREIS_OBERALLGAEU)
        self.doWork(self.dwd)
        self.dwd.readContent()
        self.dwd.dumpStatus()
        self.assertTrue(self.dwd.needsUpdate(), "fresh init so we need an update")

    def test_Kreis_Oberhavel(self):
        """
        takes standrad warncell from common config and tests it
        """

        config = configparser.ConfigParser()
        config.read_file(codecs.open(r"./test/common_config.ini", encoding="utf-8"))
        self.dwd = self.readAndCreate(aConfig=config, aSection=CONFIG_SECTION_KREIS_OBERHAVEL)
        self.doWork(self.dwd)
        self.dwd.readContent()
        self.dwd.dumpStatus()
        self.assertTrue(self.dwd.needsUpdate(), "fresh init so we need an update")

    def test_Stadt_Greiz(self):
        """
        takes warncell for Stadt Greiz
        """

        config = configparser.ConfigParser()
        config.read_file(codecs.open(r"./test/common_config.ini", encoding="utf-8"))
        self.dwd = self.readAndCreate(aConfig=config, aSection=CONFIG_SECTION_STADT_GREIZ)
        self.doWork(self.dwd)
        self.dwd.readContent()
        self.dwd.dumpStatus()
        self.assertTrue(self.dwd.needsUpdate(), "fresh init so we need an update")

    def test_Stadt_Hamburg(self):
        """
        takes warncell for Stadt Greiz
        """

        config = configparser.ConfigParser()
        config.read_file(codecs.open(r"./test/common_config.ini", encoding="utf-8"))
        self.dwd = self.readAndCreate(aConfig=config, aSection=CONFIG_SECTION_STADT_HAMBURG)
        self.doWork(self.dwd)
        self.dwd.readContent()
        self.dwd.dumpStatus()
        self.assertTrue(self.dwd.needsUpdate(), "fresh init so we need an update")

    def test_Stadt_Berlin(self):
        """
        takes warncell for Stadt Greiz
        """

        config = configparser.ConfigParser()
        config.read_file(codecs.open(r"./test/common_config.ini", encoding="utf-8"))
        self.dwd = self.readAndCreate(aConfig=config, aSection=CONFIG_SECTION_STADT_BERLIN)
        self.doWork(self.dwd)
        self.dwd.readContent()
        self.dwd.dumpStatus()
        self.assertTrue(self.dwd.needsUpdate(), "fresh init so we need an update")

    def test_Stadt_Frankfurt(self):
        """
        takes warncell for Stadt Greiz
        """

        config = configparser.ConfigParser()
        config.read_file(codecs.open(r"./test/common_config.ini", encoding="utf-8"))
        self.dwd = self.readAndCreate(aConfig=config, aSection=CONFIG_SECTION_STADT_FRANKFURT)
        self.doWork(self.dwd)
        self.dwd.readContent()
        self.dwd.dumpStatus()
        self.assertTrue(self.dwd.needsUpdate(), "fresh init so we need an update")

    def test_Stadt_Frankfurt2(self):
        """
        takes warncell for Stadt Greiz
        """
        config = configparser.ConfigParser()
        config.read_file(codecs.open(r"./test/common_config.ini", encoding="utf-8"))
        self.dwd = self.readAndCreate(aConfig=config, aSection=CONFIG_SECTION_STADT_FRANKFURT2)
        self.doWork(self.dwd)
        self.dwd.readContent()
        self.dwd.dumpStatus()
        self.assertTrue(self.dwd.needsUpdate(), "fresh init so we need an update")

    def test_Stadt_FrankfurtNord(self):
        """
        takes warncell for Stadt Greiz
        """
        config = configparser.ConfigParser()
        config.read_file(codecs.open(r"./test/common_config.ini", encoding="utf-8"))
        self.dwd = self.readAndCreate(aConfig=config, aSection=CONFIG_SECTION_STADT_FRANKFURT_NORD)
        self.doWork(self.dwd)
        self.dwd.readContent()
        self.dwd.dumpStatus()
        self.assertTrue(self.dwd.needsUpdate(), "fresh init so we need an update")

    def test_Stadt_FrankfurtSued(self):
        """
        takes warncell for Stadt Greiz
        """
        config = configparser.ConfigParser()
        config.read_file(codecs.open(r"./test/common_config.ini", encoding="utf-8"))
        self.dwd = self.readAndCreate(aConfig=config, aSection=CONFIG_SECTION_STADT_FRANKFURT_SUED)
        self.doWork(self.dwd)
        self.dwd.readContent()
        self.dwd.dumpStatus()
        self.assertTrue(self.dwd.needsUpdate(), "fresh init so we need an update")

    def test_Buggy_Entry(self):
        """
        takes buggy warncell  from common config and tests it
        """
        config = configparser.ConfigParser()
        config.read_file(codecs.open(r"./test/common_config.ini", encoding="utf-8"))
        self.dwd = self.readAndCreate(aConfig=config, aSection=CONFIG_SECTION_BUGGY)
        self.doWork(self.dwd, mustExist=False)
        self.assertTrue(self.dwd.hasErrorX())
        self.assertIsNotNone(self.dwd.getErrorMsg())

    def readAndCreate(self, aConfig, aSection):
        """creates a dwd object based on config

        Args:
            aConfig ([type]): [configuration holding the dwd warncell id]

        Returns:
            [Dwd]: [dwd object]
        """
        self.assertTrue(
            aConfig.has_section(aSection),
            "we need this set up:  " + aSection,
        )
        cellId = aConfig.get(aSection, "cellId")
        region = aConfig.get(aSection, "region")
        rT: RegionType = RegionType.getByName(region)
        aDwd = Dwd(dwdWarnCellId=cellId, regionType=rT)
        return aDwd

    def doWork(self, aDwd: Dwd, mustExist: bool = True):
        """quickly checks and read content from internet

        Args:
            aDwd (Dwd): the object to test
        """

        self.assertIsNotNone(aDwd, "We do not an object of bsr, otherwise no tests are possible")
        aDwd.dumpConfig()
        self.assertEquals(aDwd.doesWarnCellExist(), mustExist)
        aDwd.dumpStatus()
        self.assertEquals(aDwd.readContent(), mustExist)
        aDwd.dumpStatus()
        self.assertTrue(self.dwd.needsUpdate(), "fresh init so we need an update")
        self.assertEquals(aDwd.readContent(), mustExist)
        # self.assertFalse(self.dwd.needsUpdate(), "quick re-read should not force a need for update")
        self.assertTrue(self.dwd.needsUpdate(), "no optimization done - so always update")
        t = aDwd.getAlarmText()
        self.assertIsNotNone(t)
        i = aDwd.getAlarmLevel()
        self.assertIsNotNone(i)
        # logging.getLogger().info("#onHeartBeat: test for fp")
        logging.getLogger().info("Level: {}:\t{}".format(i, t))
        logging.getLogger().info(aDwd.getSummary())


if "__main__" == __name__:
    unittest.main()
