define([
    'app',
    '../templates/dwd/leaflet'
],
    function (app) {
        'use strict';
        app.component('dwdPlugin', {
            templateUrl: 'app/dwd/dwd.html',
            // controller: function ($scope, domoticzApi) {
            //     var $ctrl = this;
            //     $ctrl.message = 'This is my dwd 3 plugin'
            // }
            controller: DwdPluginController
        });

        //API
        app.factory('dwdApi', function ($q, $rootScope, domoticzApi, deviceApi) {
            var deviceIdx = 0;
            var pluginIdx = 0;

            return {
                setControlDeviceIdx: setControlDeviceIdx,

            };

            function setControlDeviceIdx(idx) {
                deviceIdx = idx;

                deviceApi.getDeviceInfo(idx).then(function (data) {
                    pluginIdx = data.HardwareID
                    console.log("got plugin idx:" + pluginIdx)
                });
            } //setControlDeviceIdx
        }); //app.factory
        //
        function DwdPluginController($element, $scope, Device, domoticzApi, deviceApi, dzNotification, dwdApi) {
            var $ctrl = this;
            $ctrl.message = 'This is my dwd 3 plugin'
            $ctrl.selectPlugin = selectPlugin;
            $ctrl.fetchDwdDevices = fetchDwdDevices;
            $ctrl.refreshDomoticzDevices = refreshDomoticzDevices;

            $ctrl.$onInit = function () {
                $ctrl.selectedApiDeviceIdx = null;
                $ctrl.selectedApiPluginIdx = null;
                $ctrl.devices = [];

                refreshDomoticzDevices().then(function () {
                    console.log("refreshDomoticzDevices");
                    // make sure only correct unit will be added, we just need one to fetch plugin / hardware name
                    $ctrl.pluginApiDevices = $ctrl.devices.filter(function (device) {
                        return device.Unit === 1
                    });

                    if ($ctrl.pluginApiDevices.length > 0) {
                        console.log("found multiple hardware for this plugin")
                        $ctrl.selectPlugin($ctrl.pluginApiDevices[0].idx);
                    }
                });

            };

            function selectPlugin(apiDeviceIdx) {
                console.log("selectPlugin: based on device idx: " + apiDeviceIdx)
                $ctrl.selectedApiDeviceIdx = apiDeviceIdx;
                dwdApi.setControlDeviceIdx(apiDeviceIdx);

                $ctrl.controllerInfo = null;
                $ctrl.dwdDevices = null;

                fetchControllerInfo(apiDeviceIdx)
                    .then(function () {
                        return fetchDwdDevices($ctrl.selectedApiPluginIdx);
                    });

            }

            function fetchControllerInfo(apiDeviceIdx) {
                return deviceApi.getDeviceInfo(apiDeviceIdx).then(function (data) {
                    $ctrl.controllerInfo = data;
                    $ctrl.selectedApiPluginIdx = data.HardwareID
                    console.log("fetchControllerInfo set plugin id:", $ctrl.selectedApiPluginIdx)
                });
            }

            function fetchDwdDevices(selectedApiPluginIdx) {
                console.log("fetchDwdDevices for plugin: ", selectedApiPluginIdx, $ctrl.selectedApiPluginIdx);

                return refreshDomoticzDevices().then(function (selectedApiPluginIdx) {
                    console.log("reading in refreshDomoticzDevices - search for: ", $ctrl.selectedApiPluginIdx);
                    // make sure only correct unit will be added, we just need one to fetch plugin / hardware name
                    $ctrl.dwdDevices = $ctrl.devices.filter(function (device, selectedApiPluginIdx) {
                        console.log("check ", device.HardwareID, $ctrl.selectedApiPluginIdx, (device.HardwareID === $ctrl.selectedApiPluginIdx))
                        return device.HardwareID === $ctrl.selectedApiPluginIdx
                    });


                });


            }
            // fnc fetchDwdDevices

            function refreshDomoticzDevices() {
                console.log("refreshDomoticzDevices");
                // TODO we could at least set &utility
                return domoticzApi.sendRequest({
                    type: 'devices',
                    displayhidden: 0,
                    filter: 'utility',
                    used: 'true'

                })
                    .then(domoticzApi.errorHandler)
                    .then(function (response) {
                        if (response.result !== undefined) {
                            $ctrl.devices = response.result
                                .filter(function (device) {
                                    return device.HardwareType === 'DWD Weather Alarm Plugin'
                                })
                                .map(function (device) {
                                    //HardwareId
                                    //HardwareName
                                    //Name
                                    //Data
                                    //idx
                                    console.log("found device: ", device.Name, device.idx);
                                    return new Device(device)
                                })
                        } else {
                            $ctrl.devices = [];
                        }
                    });
            }// fnc refreshDomoticzDevices
        };// DwdPluginController


        // tab and panes

        app.component('dwdTabs', {
            transclude: true,
            controller: function MyTabsController() {
                var panes = this.panes = [];
                this.select = function (pane) {
                    angular.forEach(panes, function (pane) {
                        pane.selected = false;
                    });
                    pane.selected = true;
                };
                this.addPane = function (pane) {
                    if (panes.length === 0) {
                        this.select(pane);
                    }
                    panes.push(pane);
                };
            },
            templateUrl: 'app/dwd/dwdTabs.html'
        })
            .component('dwdPane', {
                transclude: true,
                require: {
                    tabsCtrl: '^dwdTabs'
                },
                bindings: {
                    pluginIdx: '<',
                    deviceIdx: '<',
                    devices: '<',
                    title: '@',
                    onSelect: '&',
                    onUpdate: '&'
                },
                controller: function () {
                    this.$onInit = function () {
                        this.tabsCtrl.addPane(this);
                        console.log(this);
                    };
                },
                templateUrl: 'app/dwd/dwdPane.html'
            });
    });
