###############################
#  plugin for dwd
#
# Author: belze
#
"""
<plugin key="DWDWeatherAlarm" name="DWD Weather Alarm Plugin"
    author="belze" version="0.0.4"
    externallink="https://github.com/belzetrigger/domoticz-DWDWeatherAlarm" >
    <description>
        <h2>DWD Weather Alarm</h2><br/>
        Reads warning from Deutsche Wetter Dienst (DWD) and shows warning
        inside Domoticz
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>uses the more detailed geoservice from DWD for the alerts</li>
            <li>supports different kind of data sets like: Stadt, Gemeinde,
            Landkreis</li>
            <li>name of the location will be append to created devices</li>
            <li>two devices created, one for current alerts one for future</li>
            <li>show inline icon matching to alert type</li>
            <li>show color matching to alert severity</li>
            <li>device name is updated by most sever event name</li>

        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>alarm switch current - shows warning that are marked as
            immediate</li>
            <li>alarm switch future - shows warning for the future -
            so not immediate</li>
        </ul>
        <h3>Configuration</h3>
        For more details or examples see ReadMe at github.
        <ul style="list-style-type:square">
            <li>WarnCellId - the official warncell Id from DWD see eg.
            102000000 for Hamburg see:
            <a href="https://www.dwd.de/DE/leistungen/opendata/help/warnungen/cap_warncellids_csv.html">WarncellId CSV</a></li>
            <li>RegionType - the matching region type for this warn cell. eg.
            Landkreise</li>
            <li>Details - define what to show: name, icon, description </li>
        </ul>



    </description>
    <params>
        <param field="Mode1" label="WarnCell Id" width="200px"
        required="true" default="102000000"/>
        <param field="Mode2" label="RegionType" width="200px">
            <options>
                <option label="Landkreise" value="Kreis" />
                <option label="Gemeinde" value="Gemeinde"/>
                <option label="Kueste" value="KUESTE"/>
                <option label="Binnenseen" value="Binnensee"/>
                <option label="Nord- und Ostsee" value="SEE"/>

            </options>
        </param>
        <param field="Mode3" label="details" width="200px">
            <options>
                <option label="event name with icon" value="event_icon"/>
                <option label="only event name" value="event" />
                <option label="event name, icon, details"
                value="event_icon_details"/>
                <option label="eventname, details" value="event_details"/>
            </options>
        </param>
        <param field="Mode4" label="Update every x minutes" width="200px"
        required="true" default="30"/>

        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="False" value="Normal" />
                <option label="True" value="Debug"/>
                <option label="with Test" value="Debug Test"  />
            </options>
        </param>

    </params>
</plugin>
"""
# test own html page
import os

# import datetime as dt
from datetime import datetime, timedelta
from shutil import copy2, rmtree

try:
    import Domoticz  # type: ignore
except ImportError:
    from blz import fakeDomoticz as Domoticz
    from blz.fakeDomoticz import Devices, Images, Parameters

from blz import blzHelperInterface
from dwd.dwd import Dwd, DwdDetailLevel, RegionType

DWD_PARAM_PASS = "123"

# minimum time in min to fetch new data
DWD_POLL_THRESHOLD_MIN_MINUTES = 5
# max time in min to fetch new data aka 3h days
DWD_POLL_THRESHOLD_MAX_MINUTES = 3 * 60
DWD_DEFAULT_POLL_INTERVAL_MINUTES = DWD_POLL_THRESHOLD_MIN_MINUTES
# standard mode to show in domoticz
DWD_DEFAULT_DETAIL_LEVEL = DwdDetailLevel.EVENT_ICON
DWD_DEFAULT_DEBUG = False
DWD_DEFAULT_TEST = False
# default timeout value for requests
DWD_DEFAULT_TIMEOUT = 15

DWD_UNIT_NOW_SWITCH_IDX = 1    # unit index for current warning
DWD_UNIT_FUTURE_SWITCH_IDX = 2  # unit index for future

DWD_UNIT_NOW_NAME_SUFFIX = " (IMM)"
DWD_UNIT_FUTURE_NAME_SUFFIX = " (FUTR)"

DWD_PLUGIN_NAME = "DWDWeatherAlarm"
DWD_HTML_NAME = "html/{}.html".format(DWD_PLUGIN_NAME.lower())


class BasePlugin:
    enabled = False

    def __init__(self):
        self.dwd: Dwd = None
        self.debug = False
        self.test = False
        self.error = False
        self.nextpoll = datetime.now()
        self.pollinterval = DWD_DEFAULT_POLL_INTERVAL_MINUTES
        self.errorCounter = 0
        self.regionType: RegionType = None
        self.warncellId: str = None
        self.region: str = None
        self.detailLevel: DwdDetailLevel = None
        return

    def onStart(self):
        Domoticz.Log("onStart called")
        if blzHelperInterface.containsDebug(Parameters["Mode6"]):
            self.debug = True
            Domoticz.Debugging(1)
            DumpConfigToLog()
        else:
            Domoticz.Debugging(0)

        self.test = blzHelperInterface.containsTest(Parameters["Mode6"])

        # check polling interval parameter
        try:
            temp = int(Parameters["Mode4"])
        except:
            Domoticz.Error("Invalid polling interval parameter")
        else:
            if temp < DWD_POLL_THRESHOLD_MIN_MINUTES:
                # minimum polling interval
                temp = DWD_POLL_THRESHOLD_MIN_MINUTES
                Domoticz.Error(
                    "Specified polling interval too short: changed to {}".
                    format(DWD_POLL_THRESHOLD_MIN_MINUTES)
                )
            elif temp > DWD_POLL_THRESHOLD_MAX_MINUTES:
                # maximum polling interval is 1 hour
                temp = DWD_POLL_THRESHOLD_MAX_MINUTES
                Domoticz.Error(
                    "Specified polling interval too long: changed to {} hour".
                    format(DWD_POLL_THRESHOLD_MAX_MINUTES)
                )
            self.pollinterval = temp * 60
        Domoticz.Log("Using polling interval of {} seconds".format(
            str(self.pollinterval)))

        self.warncellId = Parameters["Mode1"]
        self.region = Parameters["Mode2"]

        if blzHelperInterface.isBlank(self.warncellId) or blzHelperInterface.isBlank(self.region):
            Domoticz.Error(
                "No warncellId / regionType set - please update setting.")
            raise ValueError("warncellId and regionType must be given.")
        else:
            self.regionType = RegionType.getByName(self.region)
        # check detail level
        if blzHelperInterface.isBlank(Parameters["Mode3"]):
            Domoticz.Error(
                "No Detail level defined use default: {}".format(
                    DWD_DEFAULT_DETAIL_LEVEL.name)
            )
            self.detailLevel: DwdDetailLevel = DWD_DEFAULT_DETAIL_LEVEL
        else:
            self.detailLevel: DwdDetailLevel = DwdDetailLevel.getByName(
                Parameters["Mode3"])
        Domoticz.Debug("Use detail level: {}".format(self.detailLevel.name))

        # TODO check images

        # TODO create device now and feature
        # Check if devices need to be created
        createDevices()

        # init with empty data
        updateDevice(DWD_UNIT_NOW_SWITCH_IDX, 0, "No Data",
                     "DWD" + DWD_UNIT_NOW_NAME_SUFFIX)
        updateDevice(DWD_UNIT_FUTURE_SWITCH_IDX, 0, "No Data",
                     "DWD" + DWD_UNIT_FUTURE_NAME_SUFFIX)

        self.defName = None
        # init and check dwd
        # self.dwd = cDwd(self.warncellId, self.regionType, self.detailLevel,
        # self.debug, self.test)
        self.dwd = self.createHelper()
        # TODO dwd can be still None!!!!
        #      maybe lets check config on hearbeat is better

        Domoticz.Debug("check if configuration fits...")
        if self.dwd and self.dwd.doesWarnCellExist():
            Domoticz.Log("DWD Configuration allright - continue")
            # show name
            n = self.dwd.getDeviceName()
            updateDevice(DWD_UNIT_NOW_SWITCH_IDX, 0, "No Data",
                         n + DWD_UNIT_NOW_NAME_SUFFIX)
            updateDevice(DWD_UNIT_FUTURE_SWITCH_IDX, 0, "No Data",
                         n + DWD_UNIT_FUTURE_NAME_SUFFIX)

        else:
            Domoticz.Error("Please verify configuration and look into logs.")
            msg: str = "Wrong Configuration"
            # check for error detail
            if (self.dwd and self.dwd.hasErrorX):
                msg = self.dwd.getErrorMsg()

            updateDevice(
                DWD_UNIT_NOW_SWITCH_IDX,
                0,
                msg,
                "DWD" + DWD_UNIT_NOW_NAME_SUFFIX,
            )
            updateDevice(
                DWD_UNIT_FUTURE_SWITCH_IDX,
                0,
                msg,
                "DWD" + DWD_UNIT_FUTURE_NAME_SUFFIX,
            )
            # TODO auf NONE setzen oder nicht?
            # self.dwd = None

        if self.debug is True and self.dwd is not None:
            self.dwd.dumpConfig()
        else:
            Domoticz.Debug("dwd is None")

        self.htmlSource = "./plugins/{}/{}".format(
            DWD_PLUGIN_NAME, DWD_HTML_NAME)
        self.htmlTarget = './www/templates/{}.html'.format(DWD_PLUGIN_NAME)

        self.install()

    def onStop(self):
        Domoticz.Log("onStop called")
        if self.dwd is not None:
            self.dwd.stop()
        self.uninstall()

    def install(self):
        Domoticz.Log('Installing plugin custom page...')

        try:
            source_path = Parameters['HomeFolder'] + 'html'
            templates_path = Parameters['StartupFolder'] + 'www/templates'
            dst_plugin_path = templates_path + '/dwdWeatherAlarm'

            Domoticz.Debug('Copying files from ' +
                           source_path + ' to ' + templates_path)

            if not (os.path.isdir(dst_plugin_path)):
                os.makedirs(dst_plugin_path)

            copy2(source_path + '/dwdWeatherAlarm.html', templates_path)
            copy2(source_path + '/dwdWeatherAlarm.js', templates_path)
            # Libs
            copy2(source_path + '/libs/leaflet.js', dst_plugin_path)
            copy2(source_path + '/libs/leaflet.css', dst_plugin_path)

            Domoticz.Log('Installing plugin custom page completed.')
        except Exception as e:
            Domoticz.Error('Error during installing plugin custom page')
            Domoticz.Error(repr(e))

    def uninstall(self):
        Domoticz.Log('Uninstalling plugin custom page...')

        try:
            templates_path = Parameters['StartupFolder'] + 'www/templates'
            dst_plugin_path = templates_path + '/dwdWeatherAlarm'

            Domoticz.Debug('Removing files from ' + templates_path)

            if (os.path.isdir(dst_plugin_path)):
                rmtree(dst_plugin_path)

            if os.path.exists(templates_path + "/dwdWeatherAlarm.html"):
                os.remove(templates_path + "/dwdWeatherAlarm.html")

            if os.path.exists(templates_path + "/dwdWeatherAlarm.js"):
                os.remove(templates_path + "/dwdWeatherAlarm.js")

            Domoticz.Log('Uninstalling plugin custom page completed.')
        except Exception as e:
            Domoticz.Error('Error during uninstalling plugin custom page')
            Domoticz.Error(repr(e))

    def createHelper(self) -> Dwd:
        newDwd: Dwd = None
        if (self.regionType and self.warncellId):
            # deeper check for details
            if (self.detailLevel is not None and self.debug is not None and
                self.test is not None):
                newDwd = Dwd(
                    self.warncellId, self.regionType, self.detailLevel,
                    self.debug, self.test,
                    DWD_DEFAULT_TIMEOUT
                )
            else:
                Domoticz.Error(
                    "Not complet hardware configuration, use defaults")
                newDwd = Dwd(
                    self.warncellId, self.regionType, DWD_DEFAULT_DETAIL_LEVEL,
                    DWD_DEFAULT_DEBUG,
                    DWD_DEFAULT_TEST, DWD_DEFAULT_TIMEOUT
                )

        else:
            Domoticz.Error(
                (
                    "Buggy settings, we cannot create Helper for DWD. "
                    "Please check hardware configuration"
                )
            )
        return newDwd

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log(
            "onCommand called for Unit: {} Parameter '{}', Level: {}".format(
                Unit, Command, Level)
        )

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound,
                       ImageFile):
        Domoticz.Log(
            (
                "Notification: Name: {}, Subject: {}, Text: {}, Status: {},"
                "Priority: {}, Sound: {}, ImageFile: {} "
            ).format(Name, Subject, Text, Status, Priority, Sound, ImageFile)
        )

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called")
        myNow = datetime.now()
        if myNow >= self.nextpoll:
            Domoticz.Debug(
                "----------------------------------------------------")

            # TODO handle dwd is None
            if self.dwd is None:
                Domoticz.Error(
                    "Dwd is None. Try to recreate. And wait for next polltime")
                self.dwd = self.createHelper()
                # self.dwd.doesWarnCellExist() better not interaction

            self.nextpoll = myNow + timedelta(seconds=self.pollinterval)

            # read info it it is time
            self.dwd.readContent()

            # check for error
            if self.dwd is None or self.dwd.hasErrorX() is True:
                self.errorCounter += 1
                if self.errorCounter % 10 == 0:
                    Domoticz.Error(
                        "got {} times an error, wait 10 min before try again"
                        .format(
                            self.errorCounter
                        )
                    )
                    # TODO maybe reset?
                    self.dwd.reset()
                    self.nextpoll = myNow + timedelta(minutes=10)
                    return

                Domoticz.Error(
                    "Uuups. Something went wrong ... Shouldn't happen")
                t = "Error"
                if self.debug is True and self.dwd is not None:
                    Domoticz.Debug(self.dwd.getSummary())
                if self.dwd is not None and self.dwd.hasErrorX() is True:
                    t = "{}:{}".format(t, self.dwd.getErrorMsg())

                updateDeviceByUnit(
                    DWD_UNIT_NOW_SWITCH_IDX, 0, t, "Error" +
                    DWD_UNIT_NOW_NAME_SUFFIX
                )
                updateDeviceByUnit(
                    DWD_UNIT_FUTURE_SWITCH_IDX, 0, t, "Error" +
                    DWD_UNIT_FUTURE_NAME_SUFFIX
                )

                self.nextpoll = myNow
            else:
                self.errorCounter = 0

                if self.dwd.needsUpdate() is True:
                    alarmLevel = self.dwd.getAlarmLevel()
                    summary = self.dwd.getAlarmText()
                    name = self.dwd.getDeviceName()
                    # TODO as we change name but updateDevice is not checking
                    # this, we say alwaysUpdate
                    updateDevice(
                        DWD_UNIT_NOW_SWITCH_IDX,
                        alarmLevel,
                        summary,
                        name + DWD_UNIT_NOW_NAME_SUFFIX,
                        True,
                    )

                    alarmLevelFut = self.dwd.getAlarmLevelFuture()
                    summaryFut = self.dwd.getAlarmTextFuture()
                    nameFut = self.dwd.getDeviceNameFuture()

                    # TODO as we change name but updateDevice is not checking
                    # this, we say alwaysUpdate
                    updateDevice(
                        DWD_UNIT_FUTURE_SWITCH_IDX,
                        alarmLevelFut,
                        summaryFut,
                        nameFut + DWD_UNIT_FUTURE_NAME_SUFFIX,
                        True,
                    )
                    self.lastUpdate = myNow
                # only on success set next poll time, so on error, we run it
                # next heartbeat
                self.nextpoll = myNow + timedelta(seconds=self.pollinterval)

            Domoticz.Debug(
                "----------------------------------------------------")


global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onStop():
    global _plugin
    _plugin.onStop()


def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status,
                           Priority, Sound, ImageFile)


def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()


# Generic helper functions


def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            value: str = str(Parameters[x])
            if x == DWD_PARAM_PASS:
                value = "xxx"
            Domoticz.Debug("{}:\t{}".format(x, value))
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           {} - {}".format(x, str(Devices[x])))
        Domoticz.Debug("Device ID:       '{}'".format(Devices[x].ID))
        Domoticz.Debug("Device Name:     '{}'".format(Devices[x].Name))
        if hasattr(Devices[x], "nValue"):
            Domoticz.Debug("Device nValue:    {}".format(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '{}'".format(Devices[x].sValue))
        if hasattr(Devices[x], "LastLevel"):
            Domoticz.Debug("Device LastLevel: {}".format(Devices[x].LastLevel))
    return


def checkImages(sName: str, sZip: str):
    Domoticz.Debug("Make sure images {} {}".format(sName, sZip))
    # Check if images are in database
    if sName not in Images:
        Domoticz.Image(sZip).Create()


def updateDeviceByUnit(
    Unit: int, alarmLevel, alarmData, name: str = "", dscr: str = "",
    alwaysUpdate=False
):
    """standard update with unit number.
       Device will only be updated only if values are changed or
       alwaysUpdate = True

    Arguments:
        Unit {int} -- unit number of the device to update
        alarmLevel {[type]} -- also nValue, for switch 0 = off, 1 = on
        alarmData {[type]} -- also sValue, textual data

    Keyword Arguments:
        name {str} -- name of the device (default: {''})
        dscr {str} -- description (default: {''})
        alwaysUpdate {bool} -- if true, always force update (default: {False})
    """
    Domoticz.Debug("updateDeviceByUnit: unit {}, name {} ".format(Unit, name))

    # Make sure that the Domoticz device still exists (they can be deleted)
    # before updating it
    if Unit in Devices:
        if (alarmData != Devices[Unit].sValue
            ) or (int(alarmLevel) != Devices[Unit].nValue or
                  alwaysUpdate is True):
            if not name:
                Devices[Unit].Update(
                    int(alarmLevel), alarmData, Description=dscr)
            else:
                Devices[Unit].Update(
                    int(alarmLevel), alarmData, Name=name, Description=dscr)

            Domoticz.Log(
                "Update #{} Name: {} nV: {} sV: {}  ".format(
                    Unit, Devices[Unit].Name, str(alarmLevel), str(alarmData)
                )
            )
        else:
            Domoticz.Log("BLZ: Remains Unchanged")
    else:
        Domoticz.Error(
            "Devices[{}] is unknown. So we cannot update it.".format(Unit))


def updateImageByUnit(Unit: int, picture):
    """push a new image to given device.
       standard way using unit number to find matching entry/device.
       If unit does not exist print error log and do nothing.
    Arguments:
        Unit {int} -- number of this device
        picture {[type]} -- picture to use
    """
    Domoticz.Debug("Image: Update Unit: {} Image: {}".format(Unit, picture))
    if Unit in Devices and picture in Images:
        Domoticz.Debug("Image: Name:{}\tId:{}".format(
            picture, Images[picture].ID))
        if Devices[Unit].Image != Images[picture].ID:
            Domoticz.Log(
                ("Image: Device Image update: 'Fritz!Box', Currently {}, "
                 "should be {} "
                 ).format(str(Devices[Unit].Image), str(Images[picture].ID))
            )
            Devices[Unit].Update(
                nValue=Devices[Unit].nValue,
                sValue=str(Devices[Unit].sValue),
                Image=Images[picture].ID
            )
            # Devices[Unit].Update(int(alarmLevel), alarmData, Name=name)
    else:
        Domoticz.Error(
            "BLZ: Image: Unit or Picture {} unknown".format(picture))
        Domoticz.Error("BLZ: Number of icons loaded = " + str(len(Images)))
        for image in Images:
            Domoticz.Error(
                "Image: {} id: {} name: {}".format(
                    image, Images[image].ID, Images[image].Name)
            )
    return


#############################################################################
#                       Device specific functions                           #
#############################################################################


def createDevices():
    """
    this creates the alarm device for warning
    """
    # create the mandatory child devices if not yet exist
    if DWD_UNIT_NOW_SWITCH_IDX not in Devices:
        Domoticz.Device(
            Name="DWD Immediate", Unit=DWD_UNIT_NOW_SWITCH_IDX,
            TypeName="Alert", Used=1
        ).Create()
        Domoticz.Log("Devices[{}] created.".format(DWD_UNIT_NOW_SWITCH_IDX))
    if DWD_UNIT_FUTURE_SWITCH_IDX not in Devices:
        Domoticz.Device(
            Name="DWD Future", Unit=DWD_UNIT_FUTURE_SWITCH_IDX,
            TypeName="Alert", Used=1
        ).Create()
        Domoticz.Log("Devices[{}] created.".format(DWD_UNIT_FUTURE_SWITCH_IDX))


#
def updateDevice(Unit, alarmLevel, alarmData, name="", alwaysUpdate=False):
    """update a device - means today or tomorrow, with given data.
    If there are changes and the device exists.
    Arguments:
        Unit {int} -- index of device, 1 = today, 2 = tomorrow
        highestLevel {[type]} -- the maximum warning level for that day,
        it is used to set the domoticz alarm level
        alarmData {[str]} -- data to show in that device, aka text

    Optional Arguments:
        name {str} -- optional: to set the name of that device,
        eg. mor info about  (default: {''})
        alwaysUpdate {bool} -- optional: to ignore current status/needs update
        (default: {False})
    """

    # Make sure that the Domoticz device still exists (they can be deleted)
    # before updating it
    if Unit in Devices:
        if (alarmData != Devices[Unit].sValue
            ) or (int(alarmLevel) != Devices[Unit].nValue or
                  alwaysUpdate is True):
            if len(name) <= 0:
                Devices[Unit].Update(int(alarmLevel), alarmData)
            else:
                Devices[Unit].Update(nValue=int(
                    alarmLevel), sValue=alarmData, Name=name)
            Domoticz.Log("BLZ: Updated to: {} value: {}".format(
                alarmData, alarmLevel))
        else:
            Domoticz.Log("BLZ: Remains Unchanged")
    else:
        Domoticz.Error(
            "Devices[{}] is unknown. So we cannot update it.".format(Unit))
