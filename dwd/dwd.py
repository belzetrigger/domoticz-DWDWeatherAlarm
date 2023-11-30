import random
from datetime import datetime
from typing import List

import requests
from requests.models import Response

# import os

try:
    import Domoticz  # type: ignore # python.analysis.warnings:
except ImportError:
    from blz import fakeDomoticz as Domoticz

from enum import Enum, unique

from blz.blzHelperInterface import hex_to_rgb, isBlank, parseIsoDate

# import rpdb
# rpdb.set_trace()

# https://maps.dwd.de/geoserver/dwd/ows?service=WFS&version=2.0.0&request=GetFeature&typeName={region_type}&CQL_FILTER=WARNCELLID=%27{warncellid}%27&OutputFormat=application/json
# https://maps.dwd.de/geoserver/dwd/ows?service=WFS&version=2.0.0&request=GetFeature&typeName={region_type}&CQL_FILTER={cql_filter_property}=%27{warncellid}%27&OutputFormat=application/json

SERVER_PROD = "https://maps.dwd.de/geoserver/dwd/ows?"
# fall back not stable
# SERVER_FALLBACK = "https://brz-maps.dwd.de/geoserver/wfs?"
URL_CHECK = "{SERVER}service=WFS&version=2.0.0&request=GetFeature&typeName={REGION_TYPE_COMMON}&CQL_FILTER=WARNCELLID=%27{WARNCELL_ID}%27&OutputFormat=application/json"
URL_WARNING = "{SERVER}service=WFS&version=2.0.0&request=GetFeature&typeName={REGION_TYPE_WARN}&CQL_FILTER={FILTER_PROP}=%27{WARNCELL_ID}%27&OutputFormat=application/json"
# %27711000003%27

URL_ICON = "https://www.dwd.de/DWD/warnungen/warnapp_gemeinden/viewer/img/warndreieck/"
URL_ICON2 = "https://www.wettergefahren.de/stat/warnungen/warnapp/img/warnicons/"

MAX_SHOWN_DETAIL_LENGTH = 120


@unique
class DwdDetailLevel(Enum):
    EVENT = False, False
    EVENT_DETAILS = (
        True,
        False,
    )
    EVENT_ICON = False, True
    EVENT_ICON_DETAILS = True, True

    def __init__(self, details: bool, icon: bool):
        self.showDetails = details
        self.showIcon = icon

    @classmethod
    def getDefault(cls):
        return cls.EVENT_DETAILS

    @classmethod
    def getByName(cls, aName: str):
        # cls here is the enumeration
        if isBlank(aName):
            return cls.getDefault()
        return cls[(aName.upper())]  # type: ignore


class DwdIcons(Enum):
    # STURM = "warn_icons_sturm.png", [11,12,13,51,52,53,54,55,56,57,58]
    # FROST2 = "warn_icons_frost.png",[22,81,82,83,84,85,86,87]
    # NEBEL = "warn_icons_nebel.png",[59]
    # REGEN = "warn_icons_regen.png",[61,62,63,64,65,66]
    # SCHNEE = "warn_icons_schnee.png",[70,71,72,73,74,75,76,77,78]
    # GEWITTER = "warn_icons_gewitter.png", [31,33,34,36,38,40,41,42,44,45,
    #       46,48,49,95,96]
    # TAUWETTER = "warn_icons_tauwetter.png",[88,89]
    # GLATTEIS = "warn_icons_glatteis.png",[24,83,84,85,86,87]
    # HITZE = "warn_icons_hitze.png",[0]
    # UV2 = "warn_icons_uv.png",[0]
    # Icons based on EC-Group
    THUNDERSTORM = "warn_icons_gewitter.png", [
        31,
        33,
        34,
        36,
        38,
        40,
        41,
        42,
        44,
        45,
        46,
        48,
        49,
        57,
        58,
        95,
        96,
    ]
    WIND = "warn_icons_sturm.png", [
        11,
        12,
        13,
        31,
        33,
        34,
        36,
        38,
        40,
        41,
        42,
        44,
        45,
        46,
        48,
        49,
        51,
        52,
        53,
        54,
        55,
        56,
        57,
        58,
        74,
        75,
        76,
        77,
        78,
        95,
        96,
    ]
    TORNADO = "warn_icons_sturm.png", [41, 45, 49, 96]
    RAIN = "warn_icons_regen.png", [
        34,
        36,
        38,
        40,
        41,
        42,
        44,
        45,
        46,
        48,
        49,
        57,
        58,
        61,
        62,
        621,
        63,
        64,
        65,
        66,
        88,
        89,
        95,
        96,
    ]
    HAIL = "warn_icons_regen.png", [
        33,
        34,
        38,
        40,
        41,
        42,
        44,
        45,
        46,
        48,
        49,
        95,
        96,
    ]
    SNOWFALL = "warn_icons_schnee.png", [70, 71, 72, 73, 76, 77, 78]
    SNOWDRIFT = "warn_icons_schnee.png", [74, 75, 76, 77, 78]
    FOG = "warn_icons_nebel.png", [59]
    FROST = "warn_icons_frost.png", [22, 81, 82, 83]
    SLIPPERINESS = "warn_icons_glatteis.png", [24, 83, 84, 85, 86, 87]
    GLAZE = "warn_icons_glatteis.png", [24, 83, 84, 85, 86, 87]
    THAW = "warn_icons_tauwetter.png", [88, 89]

    POWERLINEVIBRATION = "warn_icons_uv.png", [79]
    UV = "warn_icons_uv.png", [246]
    HEAT = "warn_icons_hitze.png", [247, 248]
    TEST = "warn_icons_binnensee.png", [98, 99]

    BINNENSEE = "warn_icons_binnensee.png", [57, 58]
    KUESTE = "warn_icons_kueste.png", [11, 12, 13]
    HOCHSEE = "warn_icons_kueste.png", [14, 15, 16]

    # https://www.wettergefahren.de/stat/warnungen/warnapp/img/warnicons/warn_icons_binnensee.png
    # https://www.wettergefahren.de/stat/warnungen/warnapp/img/warnicons/warn_icons_kueste.png
    def __init__(self, png: str, codes: List[int]):
        self.png = png
        self.codes = codes

    def getUrl(self) -> str:
        return URL_ICON2 + self.png
        # return self.png

    @classmethod
    def getByName(cls, aName: str):
        # cls here is the enumeration
        if isBlank(aName):
            return None
        return cls[aName.upper()]  # type: ignore


@unique
class Severity(Enum):

    """the severity or level of an event"""

    # dz Level = (0=gray, 1=green, 2=yellow, 3=orange, 4=red)
    NONE = (0, 0)
    MINOR = 1, 2  # Wetterwarnung (Gelb)
    MODERATE = 2, 3  # MarkanteWetterwarnung (Orange)
    SEVERE = 3, 4  # Unwetterwarnung (Rot)
    EXTREME = 4, 4  # Extreme Unwetterwarnung (Violet)

    def __init__(self, internalValue: int, domoticzValue: int):
        """to create a member for this enum

        Args:
            internalValue (int): internal used unique value to compare
                                    the severity
            domoticzValue (int): value used within domoticz alarm/alert device
        """
        self._value_ = internalValue
        self.domoticzValue = domoticzValue

    def describe(self):
        # self is the member here
        return self.name, self.value

    def __str__(self):
        return "my custom str! {0}".format(self.name)

    @classmethod
    def getByName(cls, aName: str):
        # cls here is the enumeration
        return cls[aName.upper()]  # type: ignore

    @classmethod
    def max(cls, a: Enum, b: Enum):
        maxS = None
        if b is None or (a is not None and a.value > b.value):
            maxS = a
        elif a is None and b is not None:
            maxS = b
        else:
            maxS = b
        return maxS


@unique
class DwdAlertColor(Enum):
    # Warnungen vor extremem Unwetter (Stufe 4)
    DARK_RED = Severity.EXTREME, 0x880E4F
    # Unwetterwarnungen (Stufe 3)
    RED = Severity.SEVERE, 0xE53935
    # Warnungen vor markantem Wetter (Stufe 2)
    ORANGE = Severity.MODERATE, 0xFB8C00
    YELLOW = Severity.MINOR, 0xFFEB3B  # Wetterwarnungen (Stufe 1)
    VIOLET_HEAT_EXTREM = Severity.SEVERE, 0x9E46F8  # Hitzewarnung (extrem)
    VIOLET_HEAT = Severity.MINOR, 0xC9F  # Hitzewarnung
    VIOLET_UV = Severity.MINOR, 0xFE68FE  # UV-Warnung
    GREEN = Severity.NONE, 0xC5E566  # keine Warnung
    FUTURE = (
        Severity.NONE,
        None,
        "/stat/warnungen/warnapp/img/vorab.png",
    )

    # Vorabinformation Unwetter, lt. Doku erst ab Stufe 3 published

    def __init__(
        self, severity: Severity, hex: int, alternativeImage: str = ""
    ) -> None:
        self.severity = severity
        self.hexColor = hex
        self.alternativeImage = alternativeImage

    def getColorAsHexString(self) -> str:
        return "#{:02x}".format(self.hexColor)

    def getColorAsRGBString(self) -> str:
        return "rgb{}".format(hex_to_rgb(self.getColorAsHexString()))

    @classmethod
    def getByName(cls, aName: str):
        # cls here is the enumeration
        return cls[aName.upper()]  # type: ignore

    @classmethod
    def getBySeverity(cls, severity: Severity):
        for x in DwdAlertColor:
            if x.severity == severity:
                return x
        # cls here is the enumeration
        raise ValueError("could not find entry for " + severity.name)


@unique
class RegionTypeCommon(Enum):
    KREIS = "dwd:Warngebiete_Kreise"
    BINNENSEE = "dwd:Warngebiete_Binnenseen"
    SEE = "dwd:Warngebiete_See"
    KUESTE = "dwd:Warngebiete_Kueste"
    GEMEINDEN = "dwd:Warngebiete_Gemeinden"


@unique
class RegionTypeWarning(Enum):
    KREIS = "dwd:Warnungen_Landkreise"
    BINNENSEE = "dwd:Warnungen_Binnenseen"
    SEE = "dwd:Warnungen_See"
    KUESTE = "dwd:Warnungen_Kueste"
    GEMEINDEN = "dwd:Warnungen_Gemeinden"


@unique
class RegionType(Enum):
    KREIS = RegionTypeWarning.KREIS, RegionTypeCommon.KREIS, "GC_WARNCELLID"
    BINNENSEE = RegionTypeWarning.BINNENSEE, RegionTypeCommon.BINNENSEE
    SEE = RegionTypeWarning.SEE, RegionTypeCommon.SEE
    KUESTE = RegionTypeWarning.KUESTE, RegionTypeCommon.KUESTE
    GEMEINDE = RegionTypeWarning.GEMEINDEN, RegionTypeCommon.GEMEINDEN

    def __init__(
        self,
        warning: RegionTypeWarning,
        common: RegionTypeCommon,
        filter: str = "WARNCELLID",
    ):
        self.warning = warning  # warning type
        self.common = common  # common type
        self.filterProp = filter

    @classmethod
    def getByName(cls, aName: str):
        return cls[aName.upper()]
        # with py 3.12 buggy cls here is the enumeration
        # return cls.__getattribute__(aName.upper())  # type: ignore


class DwdData:
    def __init__(self, ftPropJson):
        self.pubTime: datetime = parseIsoDate(ftPropJson["EFFECTIVE"])
        self.startTime: datetime = parseIsoDate(ftPropJson["ONSET"])
        # TODO do we need infoId? only Landkreis do have it
        # self.infoId = ftPropJson["INFO_ID"]
        self.endTime: datetime = parseIsoDate(ftPropJson["EXPIRES"])
        self.event: str = ftPropJson["EVENT"]
        self.responsType: str = ftPropJson["RESPONSETYPE"]
        self.eventGroup: str = ftPropJson["EC_GROUP"]  # THUNDERSTORM
        self.eventColor: str = ftPropJson["EC_AREA_COLOR"]  # 255 235 59"
        self.eventCode: str = ftPropJson["EC_II"]  # 31
        self.category: str = ftPropJson["CATEGORY"]  # Met
        self.headline: str = ftPropJson["HEADLINE"]
        self.description: str = ftPropJson["DESCRIPTION"]
        self.instruction: str = ftPropJson["INSTRUCTION"]
        self.urgency: str = ftPropJson["URGENCY"]
        self.serverity: str = ftPropJson["SEVERITY"]
        self.serverityType: Severity = Severity.getByName(self.serverity)
        self.level = 0
        # "Gewitter,Gewitteraufzugsrichtung
        self.parameterName: str = ftPropJson["PARAMETERNAME"]
        # isolated,south-east"
        self.parameterValue: str = ftPropJson["PARAMETERVALUE"]
        # Kreis Oberhavel"
        self.parameterValue: str = ftPropJson["AREADESC"]

        # TODO do we need short name for Bundesland? Only Landkreise do have it
        # self.gcState=ftPropJson["GC_STATE"] #BB
        # color: "#000000"
        self.status = ftPropJson["STATUS"]

    def dumpStatus(self):
        Domoticz.Debug(self)

    def __str__(self) -> str:
        s = "{} von {:%a %d.%m. %H:%M}-{:%a %H:%M}".format(
            self.headline, self.startTime, self.endTime
        )
        return s

    def getSummary(self, seperator: str = "<br>") -> str:
        s = "{}({}) {:%a %d.%m. %H:%M}-{:%a %H:%M}".format(
            self.event, self.serverityType.value, self.startTime, self.endTime
        )
        return s


# (BlzHelperInterface):
class Dwd:
    def __init__(
        self,
        dwdWarnCellId: str,
        regionType: RegionType = RegionType.GEMEINDE,
        detailLevel: DwdDetailLevel = DwdDetailLevel.EVENT,
        debug: bool = False,
        test: bool = False,
        timeout: int = 10,
    ):
        Domoticz.Debug("create dwd for {}".format(dwdWarnCellId))
        self.warnCellId = dwdWarnCellId
        self.regionType = regionType
        self.detailLevel = detailLevel
        self.debug = debug
        self.test = test
        self.timeout: int = timeout

        # self.lastTimeStamp = None  # last time stamp from web
        # self.currentTimeSamp = None
        self.updateNeeded = True
        self.hasError = False
        # self.nextpoll = datetime.now()
        # self.immediateWarnings : List[DwdData]=[]
        # self.immediateMaxLevel: int = 0
        # self.immediateMax: Severity
        # self.futureWarnings: List[DwdData]=[]
        # self.futureMaxLevel: int = 0
        # self.futureMax: Severity
        self.reset()
        self.resetError()
        return

    def reset(self):
        # TODO
        # self.lastTimeStamp:datetime = None
        # self.currentTimeSamp:datetime = None
        self.lastReadTime: datetime = datetime(1977, 1, 1)
        self.updateNeeded = True
        self.baseDataInitialized = False
        self.shortName = None
        self.Name = None
        self.Kreis = None
        self.KreisId = None
        self.County = None
        self.CountyAbv = None
        # self.immediateWarnings : List[DwdData]=[]
        # self.immediateMaxLevel: int = 0
        # self.immediateMax: Severity
        # self.futureWarnings: List[DwdData]=[]
        # self.futureMaxLevel: int = 0
        # self.futureMax: Severity
        self.useFallbackCheck: bool = False
        self.useFallbackWarn: bool = False
        self.reinitData()
        pass

    def reinitData(self):
        self.useFallbackWarn = False
        self.immediateWarnings: List[DwdData] = []
        self.immediateMaxLevel: int = 0
        self.immediateMax: Severity = Severity.NONE
        self.immediateMaxWarning: DwdData = None
        self.futureWarnings: List[DwdData] = []
        self.futureMaxLevel: int = 0
        self.futureMax: Severity = Severity.NONE

    def dumpConfig(self):
        Domoticz.Log(
            "dwd: cell: {}\tregion: {}\tdetail: {}".format(
                self.warnCellId, self.regionType.name, self.detailLevel.name
            )
        )
        # TODO
        # for value in self.devices.values():
        #    value.dumpConfig()

    def dumpStatus(self):
        Domoticz.Debug(
            "Name:\t{}\nShortname:\t{}\nKreis:\t{} ({})\nCounty:\t{} ({})".format(
                self.Name,
                self.shortName,
                self.Kreis,
                self.KreisId,
                self.County,
                self.CountyAbv,
            )
        )
        Domoticz.Debug(
            "timeStamp:\t{:%d.%m. %H:%M} - needs update:\t {}".format(
                self.lastReadTime, self.needsUpdate()
            )
        )
        Domoticz.Debug(
            "immediate level: {}\t-\tfuture level: {}".format(
                self.immediateMaxLevel, self.futureMaxLevel
            )
        )
        for x in self.immediateWarnings:
            x.dumpStatus()
        for x in self.futureWarnings:
            x.dumpStatus()

    def getSummary(self, seperator: str = "<br>") -> str:
        s: str = ""
        isFirst = True
        for x in self.immediateWarnings:
            s = s + x.getSummary(seperator=seperator)
            if isFirst is False:
                s = s + seperator
            isFirst = False

        for x in self.futureWarnings:
            s = s + x.getSummary(seperator=seperator)
            if isFirst is False:
                s = s + seperator
            isFirst = False

        if isBlank(s):
            s = "No Data"
        return s

    def needsUpdate(self):
        return self.updateNeeded

    def doesWarnCellExist(self, server: str = SERVER_PROD, timeout: int = None) -> bool:
        """checks if the given warn cell for this region type exists. as warncell and region type must go hand in hand.

        Returns:
            bool: true if we could gather some more details
        """
        if not timeout:
            timeout = self.timeout

        success = False
        url = URL_CHECK.format(
            SERVER=server,
            REGION_TYPE_COMMON=self.regionType.common.value,
            WARNCELL_ID=self.warnCellId,
        )

        Domoticz.Debug("doesWarnCellExist url:{} ".format(url))
        response: Response = None
        try:
            response = requests.get(url, timeout=timeout)
        except requests.exceptions.ReadTimeout as e:
            Domoticz.Error(
                "doesWarnCellExist: got timeout - could not verify warncell. {}".format(
                    e
                )
            )
            self.setError("Connection Issue: - could not verify settings.")
            # switch to fallback
            # if self.useFallbackCheck is False:
            #     self.useFallbackCheck = True
            #    return self.doesWarnCellExist(SERVER_FALLBACK, 2 * self.timeout)

            return success
        Domoticz.Debug("doesWarnCellExist -> yes url:{} ".format(url))
        if response and response.status_code == 200:
            jResponse = response.json()
            features = jResponse["features"]
            totalFeatures = jResponse["totalFeatures"]
            # if( totalFeatures is not None and ((int) totalFeatures)  => 1):
            #    Domoticz.Debug("Got at least one result. So Warncell Id is alright.")
            if totalFeatures is None:
                Domoticz.Error(
                    "Looks like wrong RegionType: {}".format(self.regionType)
                )
                self.setError("Settings Issue: Please verify setting eg. RegionType.")

            elif totalFeatures >= 1:
                Domoticz.Debug("Looks like correct WarnCellId and Region")
                prop = features[0]["properties"]
                self.setDetails(prop)
                success = True
                if totalFeatures > 1:
                    Domoticz.Log(
                        "Looks like we found more entries - but we just take the first!"
                    )

        else:
            if response and response.status_code >= 500:
                Domoticz.Error(
                    "Looks Server issue for Url={} code={} ".format(
                        url, response.status_code
                    )
                )
                self.setError("Connection Issue: - could not verify settings.")
            else:
                Domoticz.Error(
                    "Looks like unknown error: invalid WarnCell Id - Please check. Url={}. Error: {}. We will check for alternative server. ".format(
                        url, response.content
                    )
                )

                # if self.useFallbackCheck is False:
                #    self.useFallbackCheck = True
                #    return self.doesWarnCellExist(
                #        SERVER_FALLBACK, timeout=self.timeout * 2
                #    )
                # else:
                self.setError(
                    "Connection Issue: - could not verify settings. Details={}".format(
                        response.content
                    )
                )

        return success

    def setDetails(self, prp):
        """extract some details for given warncell based on passed properties.

        Args:
            prp (json): the json properties of the warn cell
        """
        if prp:
            self.shortName = prp["KURZNAME"]
            self.Name = prp["NAME"]
            self.baseDataInitialized = True
            try:
                self.Kreis = prp["KREIS"]
                self.KreisId = prp["KRSID"]
                self.County = prp["BL"]
                self.CountyAbv = prp["BL_KUERZEL"]
            except Exception as e:
                Domoticz.Debug("No data for Kreis, Error: {}".format(e))

    def readContent(self, server: str = SERVER_PROD, timeout: int = None) -> bool:
        # if(self.baseDataInitialized is False):
        #    self.setError("Please init via 'doesWarnCellExist()' DWD first")
        #    return

        if not timeout:
            timeout = self.timeout

        # maybe better just call it self
        success: bool = False
        try:
            if self.baseDataInitialized is False:
                Domoticz.Debug(
                    "Looks like wrong order - check and init via 'doesWarnCellExist()' were missing "
                )
                if self.doesWarnCellExist() is False:
                    raise ValueError(
                        "Check configuration WarnCellId for this region could not verified."
                    )

            # TODO for now no optimization, so reset data, if connection problem - old data is lost

            self.reinitData()
            self.resetError()
            self.lastReadTime = datetime.now()
            url = URL_WARNING.format(
                SERVER=server,
                REGION_TYPE_WARN=self.regionType.warning.value,
                FILTER_PROP=self.regionType.filterProp,
                WARNCELL_ID=self.warnCellId,
            )
            Domoticz.Debug("readContent url={}".format({url}))

            response: Response = None
            # TODO eigener try catch?
            # try:
            response = requests.get(url, timeout)
            # except requests.exceptions.ReadTimeout as e:
            #    Domoticz.Error(
            #        "doesWarnCellExist: got timeout - could not verify warncell. retry later. {}".
            #        format(e)
            #    )

            if response and response.status_code == 200:
                jResponse = response.json()
                features = jResponse["features"]
                totalFeatures = jResponse["totalFeatures"]
                if totalFeatures is None:
                    raise Exception(
                        "Fetched content looks wrong - no totalFeatures?! {}".format(
                            url
                        )
                    )

                for ft in features:
                    self.parseWarning(ft)
                success = True
                self.updateNeeded = True
                Domoticz.Debug(
                    "no optimized reading implemented jet - so always update needed"
                )

                # check timestamp
                # if( self.lastTimeStamp is None or self.lastTimeStamp < self.currentTimeSamp):
                #     Domoticz.Log("New Data or init - parse them....")
                #     #TODO maybe optimize init/updating of warnings
                #     for ft in features:
                #         self.readWarning(ft)
                #     self.lastTimeStamp = self.currentTimeSamp
                #     self.updateNeeded = True
                # else:
                #     self.updateNeeded = False
                #     Domoticz.Debug("no new data")

            else:
                Domoticz.Error("Could not fetch content from {}. ".format(url))
                raise Exception("Could not fetch content from {}".format(url))

            pass
        except Exception as e:
            Domoticz.Error("Error during reading and parsing {}".format(e))

            self.setError(e)
            # if self.useFallbackWarn is False:
            #    Domoticz.Error("regarding to error - we try also alternative url. ")
            #    self.useFallbackWarn = True
            #    return self.readContent(SERVER_FALLBACK, timeout=self.timeout * 2)

        return success

    def parseWarning(self, ft):
        dd = DwdData(ft["properties"])
        Domoticz.Debug("readWarning {}".format(dd))
        # check if future or immediate
        if dd.urgency == "Immediate":
            self.immediateWarnings.append(dd)
            self.immediateMaxLevel = max(self.immediateMaxLevel, dd.serverityType.value)
            self.immediateMax = Severity.max(self.immediateMax, dd.serverityType)
            # TODO do it on one block
            # extract worst warning
            if dd.serverityType == self.immediateMax:
                self.immediateMaxWarning = dd

        else:
            self.futureWarnings.append(dd)
            self.futureMaxLevel = self.immediateMaxLevel = max(
                self.futureMaxLevel, dd.serverityType.value
            )
            self.futureMax = Severity.max(self.futureMax, dd.serverityType)

    def setError(self, error):
        self.hasError = True
        self.errorMsg = error

    def resetError(self):
        self.hasError = False
        self.errorMsg = None

    def hasErrorX(self):
        return self.hasError

    def getErrorMsg(self):
        return self.errorMsg

    def getAlarmLevel(self) -> int:
        # Level = (0=gray, 1=green, 2=yellow, 3=orange, 4=red)
        i = 0
        if self.immediateMax:
            i = self.immediateMax.domoticzValue
        return i

    def getAlarmLevelFuture(self) -> int:
        # Level = (0=gray, 1=green, 2=yellow, 3=orange, 4=red)
        i = 0
        if self.futureMax:
            i = self.futureMax.domoticzValue
        return i

    def getText(self, warnings: List[DwdData], seperator: str = "<br>"):
        text = ""
        isFirst = True
        for x in warnings:
            if isFirst is False:
                text = text + seperator
            warnImg: str = ""
            details = ""
            if self.detailLevel.showIcon:
                # can also be multiple entries, sometime they use ',' sometime ';'
                n = x.eventGroup.replace(",", ";")
                splits = n.split(";")
                warnColor = x.eventColor
                warnColor = warnColor.replace(" ", ",")
                for split in splits:
                    icn = DwdIcons.getByName(split)
                    if not icn:
                        Domoticz.Error("did not got an image for {}".format(split))
                    else:
                        dscr = ""
                        if self.detailLevel.showDetails:
                            dscr = self.extractDescription(x.description)
                        warnImg = (
                            "{}<img style='border: solid rgb({});'"
                            "height='20' src='{}' title='{:%a %d %H:%M}-{:%a %H:%M} {}'/>"
                        ).format(
                            warnImg,
                            warnColor,
                            icn.getUrl(),
                            x.startTime,
                            x.endTime,
                            dscr,
                        )
            else:
                # so no icon but need to put details there
                details = " " + self.extractDescription(x.description)

            text = text + warnImg + x.getSummary() + details
            isFirst = False

        if isBlank(text):
            # TODO just for Testing remove later
            if self.test:
                # icn = DwdIcons.RAIN
                icn = random.choice(list(DwdIcons))
                cl = DwdAlertColor.getBySeverity(random.choice(list(Severity)))
                warnColor = cl
                text = "No Alert <img style='border: solid {};' height='20' src='{}' />".format(
                    warnColor.getColorAsHexString(), icn.getUrl()
                )
            else:
                text = "No Alert"
        return text

    def extractDescription(self, msg: str):
        """takes the string and cut it off to fit in description

        Args:
            msg (str): the message to fit

        Returns:
            [type]: [description]
        """
        descr: str = ""
        if self.detailLevel.showDetails:
            if len(msg) > MAX_SHOWN_DETAIL_LENGTH:
                descr = msg[0:MAX_SHOWN_DETAIL_LENGTH] + "..."
            else:
                descr = msg
        return descr

    def getAlarmText(self) -> str:
        return self.getText(self.immediateWarnings)

    def getAlarmTextFuture(self) -> str:
        # TODO same icons like for current or other?
        return self.getText(self.futureWarnings)

    def getDeviceNameFuture(self) -> str:
        s: str = self.shortName
        if len(self.futureWarnings) > 0:
            s = "{}: {}".format(self.shortName, self.immediateMaxWarning.event)
        return s

    def getDeviceName(self) -> str:
        s: str = self.shortName
        if len(self.immediateWarnings) > 0:
            s = "{}: {}".format(self.shortName, self.immediateMaxWarning.event)
        return s

    def stop(self) -> None:
        self.reset()
