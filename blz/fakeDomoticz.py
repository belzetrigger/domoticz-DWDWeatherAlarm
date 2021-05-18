#
#   Buienradar.nl Weather Lookup Plugin
#
#   Frank Fesevur, 2017
#   https://github.com/ffes/domoticz-buienradar
#
#   About the weather service:
#   https://www.buienradar.nl/overbuienradar/gratis-weerdata
#
#   Very simple module to make local testing easier
#   It "emulates" Domoticz.Log() and Domoticz.Debug()
#
#from _typeshed import FileDescriptor
from typing import Any, Dict

Parameters: Dict[str, Any] = {
    "Mode1": None,
    "Mode2": None,
    "Mode3": None,
    "Mode4": None,
    "Mode5": None,
    "Mode6": "Debug"
}
Images: Dict[str, Any] = {}
Devices: Dict[int, Any] = {}


class X:

    """
    fake class
    """
    ID: str = ""
    Name: str = ""
    Unit: str = ""
    DeviceID = ""
    sValue: str = ""
    descr: str = ""
    level: int
    nValue: int
    LastLevel: int

    def __init__(self, iUnit: int, aID: str) -> None:
        self.ID = aID
        self.Name = aID
        self.Unit = aID
        self.DeviceID = aID
        self.nValue = iUnit
        self.sValue = aID
        pass

    def Create(self):
        pass

    def Update(self, nValue: int, sValue: str = "", Name: str = "", Description: str = ""):
        self.nValue = nValue
        self.sValue = sValue
        self.Name = Name
        self.descr = Description
        pass


def Image(sZip: str):
    Debug("create image: " + sZip)
    img = X(1, sZip)
    Images[sZip] = img
    return img


def Device(
    Name: str, Unit: int, TypeName: str, Used: int = 1, Switchtype: int = 18, Options: str = None
):
    x = X(Unit, str(Unit))
    Devices[Unit] = x
    return x


def Log(s):
    print(s)


def Debug(s):
    print("Debug: {}".format(s))


def Error(s):
    print("Error: {}".format(s))


def Debugging(i):
    print("Debug: turned on")
