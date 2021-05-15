# domoticz-DWD Weather Alarm

[![PyPI pyversions](https://img.shields.io/badge/python-3.7%20|%203.8%20|%203.9-blue.svg)]() 
[![Plugin version](https://img.shields.io/badge/version-0.0.1-red.svg)](https://github.com/belzetrigger/domoticz-DWDWeatherAlarm/branches/)

Yet another weather warning plugin for Domoticz. This plugin uses the data provided by the [Deutsche Wetter Dienst](https://www.dwd.de). For performance and some other reasons this plugin uses the [WFS 2.0](https://www.dwd.de/DE/leistungen/geodienste/geodienste.html). So it is possible to download an process only data the are relevant instead of dealing with a bunch of unnecessary data like with other APIs provided by DWD. 

| Device | Image | Comment |
| ------ | ----- | ------- |
| immediate | <img src='https://github.com/belzetrigger/domoticz-DWDWeatherAlarm/blob/master/resources/alert_immediate_init.png' width="300" alt="immediate init">  <br/>

<img src='https://github.com/belzetrigger/domoticz-DWDWeatherAlarm/blob/master/resources/device_immediate_minor.png' width="300" alt="immediate loaded"><br/>
<img src='https://github.com/belzetrigger/domoticz-DWDWeatherAlarm/blob/master/resources/device_immediate_minor.png' width="300" alt="immediate muliple">

| shows alerts that are marked as immediate.<br/>Using the name provided form WFS and also Icons and Alarm Color | 
| future | <img src='https://github.com/belzetrigger/domoticz-DWDWeatherAlarm/raw/master/resources/alert_future.PNG' width="300" alt="future"> | shows future alerts |

## Summary
During the last winter time it felt like that the https://www.meteoalarm.eu/ had sometimes a delay and sometimes weather warnings never popped up. So I started to checkout what we can get from the Deutscher Wetterdienst (DWD). They publish data in several ways. 
The Web Feature Server (WFS) looked much more interesting  as it supports a Query-API.

Based on a specific Warn Cell Id this plugin requests alerts from this WFS. Results are sorted into immediate and future alerts. For immediate alerts the severity aka alert level goes from level 1 up to 4. Looks like future alerts only starting at level 3. More details can be found [here](https://www.dwd.de/DE/leistungen/opendata/help/warnungen/warning_codes_pdf.html).

This plugin tries to get the corresponding alarm icon. E.g. different icons for wind, rain, .... Also the level of severity is used to colorize the border of this plugin.  

To fetch correct data correct WarnCellId and Region Type is needed. Different Region Types are treated different and under different URL. 

Alert Images are from DWD so Copyright Deutscher Wetter Dienst more see: [DWD Icons](https://www.dwd.de/DE/wetter/warnungen_aktuell/objekt_einbindung/piktogramm_node.html)

## Prepare 
- get your desired WarnCellId
  - check the [WarnCell List](https://www.dwd.de/DE/leistungen/opendata/help/warnungen/cap_warncellids_csv.html)
  - if the location name is listed multiple times, try the Ids. It can happen, that outdated Ids still listed.
  - known special is Berlin
- guess matching region type for your WarnCellId. Cell starting with 
  - `1` represent `Landkreise`
  - `2` represent `Binnenseen` but this means mainly Bodensee and lakes in Bavaria
  - `4` represent `Nord- und Ostsee`
  - `5` represent `Küste`
  - `7` or `8` represent `Gemeinden` or `Stadtteile`.
-  you can test it quickly
   -  test with Id `80978013` and region type `Gemeinde`
   https://maps.dwd.de/geoserver/dwd/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=dwd:Warngebiete_Gemeinden&CQL_FILTER=WARNCELLID=%27809780133%27&OutputFormat=application/json
   -  test with Id `109780000` and region type `Landkreis`
    https://maps.dwd.de/geoserver/dwd/ows?service=WFS&version=2.0.0&request=GetFeature&typeName=dwd:Warnungen_Landkreise&CQL_FILTER=GC_WARNCELLID=%27109780000%27&OutputFormat=application/json
- just some more details to check if the warncell id is correct - postion 2 and 3 tells you the state (Bundesland)
  - 01 Schleswig-Holstein
  - 02 Freie und Hansestadt Hamburg 
  - 03 Niedersachsen 
  - 04 Freie Hansestadt Bremen 
  - 05 Nordrhein-Westfalen 
  - 06 Hessen 
  - 07 Rheinland-Pfalz 
  - 08 Baden-Württemberg 
  - 09 Freistaat Bayern 
  - 10 Saarland 
  - 11 Berlin 
  - 12 Brandenburg 
  - 13 Mecklenburg-Vorpommern 
  - 14 Freistaat Sachsen 
  - 15 Sachsen-Anhalt 
  - 16 Freistaat Thüringen 
- Position 4-5 counties (Landkreise)
  
## Installation and Setup
- a running Domoticz: 2020.2 or 2021.1 with Python 3.7
- Python >= 3.7
- install needed python modules:
    - urllib3
    - python-dateutil
    - or even better use `sudo pip3 install -r requirements.txt` 
- clone project
    - go to `domoticz/plugins` directory 
    - clone the project
        ```bash
        cd domoticz/plugins
        git clone https://github.com/belzetrigger/domoticz-DWDWeatherAlarm.git
        ```
- or just download, unzip and copy to `domoticz/plugins` 
- restart Domoticz service
- Now go to **Setup**, **Hardware** in your Domoticz interface. There add
**DWD Weather Alert Plugin**.
### Settings
<!-- prettier-ignore -->


| Parameter     | Information                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| name          | Domoticz standard hardware name |
| WarnCellId | Id from the [CSV List](https://www.dwd.de/DE/leistungen/opendata/help/warnungen/cap_warncellids_csv.html) |
| RegionType | Mostly Gemeinde or Landkreis |
| Update | polling time in minutes |
| Debug         | if True, the log will be hold a lot more output.                                                                                                                                                                                                                                                                                                                                                                     |
## Usage
Just add your warncell / region. Check out that devices are created. Locations name will be used as device name. 
If nothing pops up, check Domoticz Logs. And try to change Id or RegionType.

## Bugs and ToDos
- [x] use name coming from WFS for devices
- [x] use icons to symbolize the event
- [x] use color to show severity
- [ ] meaning full data on image, hover, ...  
- [ ] change from online icon to offline icon
- [ ] change general device icon, so we use big icons from DWD
- [ ] support also name not only warncell
- [ ] more filter options, 
  - [ ] like certain severity level 
  - [ ] like certain group of warnings like only rain, thunderstorms 

## Versions
| Version | Note                                                                                     |
| ------- | ---------------------------------------------------------------------------------------- |
| 0.0.1  | initial version with basic functions                                  |

## State
Under development but initial version works

## Developing
Based on https://github.com/ffes/domoticz-buienradar/ there are
- `/blz/fakeDomoticz.py` - used to run it outside of Domoticz
- `/blz/blzHelperInterface.py` starting point for some more structure
- unittest under folder `/test`  - it's the entry point for tests
  - copy `sample_config.ini`  to `my_config.ini` and adapt to your liking  
  - `common_config.ini` is the standard config for different test scenarios
  - `test_dwd.py` tests the DWD class
  - `test_plugin.py` test core functions of plugin.py

## Links
### DWD Documentation:
- https://www.dwd.de/DE/wetter/warnungen_aktuell/objekt_einbindung/einbindung_karten_geodienste.pdf?__blob=publicationFile&v=14
- https://www.dwd.de/DE/leistungen/opendata/help/warnungen/dwd_warnings_products_overview_de_pdf.pdf?__blob=publicationFile&v=7
- https://www.dwd.de/DE/leistungen/opendata/help/warnungen/warning_codes_pdf.pdf?__blob=publicationFile&v=5
### similar plugins
- https://community.home-assistant.io/t/dwd-warnapp-sensor-amtliche-warnungen-des-deutschen-wetterdienstes/22699/27
- https://github.com/Hummel95/home-assistant/blob/dev/homeassistant/components/dwd_weather_warnings/sensor.py


