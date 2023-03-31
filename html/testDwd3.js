define(['angular',
    'app',
    '../templates/dwdWeatherAlarm/leaflet',
    // '../templates/dwdWeatherAlarm/test_devices',
    'app/devices/Devices.js'
],

    function (angular, app, leaflet) {


        app.component('dwdPlugin', {
            templateUrl: 'app/dwd/index.html',
            /*controller: function ($scope, domoticzApi) {
                var $ctrl = this;
                $ctrl.message = 'This is my dwd 3 plugin'
            }*/
            controller: DwdPluginController
        });

        // Allows to load Devices.html which contains templates for <devices-table /> component
        app.component('dwdFakeDevices', {
            templateUrl: 'app/devices/Devices.html',
        });


        app.factory('dwdalarm', function ($q, $rootScope, domoticzApi, deviceApi) {
            var deviceIdx = 0;
            var pluginIdx = 0;
            var requestsCount = 0;
            var requestsQueue = [];

            $rootScope.$on('device_update', function (e, device) {
                if (device.idx === deviceIdx) {
                    // handleResponse(JSON.parse(device.Data))
                    // sometimes it is json sometimes not
                    // eg for response/requests
                    t = "";
                    try {
                        t = JSON.parse(device.Data);
                        console.log("got json")

                    } catch (error) {
                        t = device;
                        console.log("got no json" + device.Data)
                    }
                    handleResponse(t);

                }
            });

            return {
                setControlDeviceIdx: setControlDeviceIdx,
                sendRequest: sendRequest,
            };

            function setControlDeviceIdx(idx) {
                deviceIdx = idx;

                deviceApi.getDeviceInfo(idx).then(function (data) {
                    pluginIdx = data.HardwareID
                    console.log("got plugin idx:" + pluginIdx)
                });

                // domoticzApi.sendCommand('clearlightlog', {
                //     idx: idx
                // }).catch(function () {
                //     console.log('Unable to clear log for device idx:' + idx)
                // });
            }

            function sendRequest(command, params) {
                var deferred = $q.defer();
                var requestId = ++requestsCount;

                var requestInfo = {
                    requestId: requestId,
                    deferred: deferred,
                };

                requestsQueue.push(requestInfo);

                domoticzApi.sendCommand('udevice', {
                    idx: deviceIdx,
                    svalue: JSON.stringify({
                        type: 'request',
                        requestId: requestId,
                        command: command,
                        params: params || {}
                    })
                }).catch(function (error) {
                    deferred.reject(error);
                });

                return deferred.promise;
            }

            function handleResponse(data) {
                if (data.type !== 'response' && data.type !== 'status') {
                    return;
                }

                var requestIndex = requestsQueue.findIndex(function (item) {
                    return item.requestId === data.requestId;
                });

                if (requestIndex === -1) {
                    return;
                }

                var requestInfo = requestsQueue[requestIndex];

                if (data.type === 'status') {
                    requestInfo.deferred.notify(data.payload);
                    return;
                }

                if (data.isError) {
                    requestInfo.deferred.reject(data.payload);
                } else {
                    requestInfo.deferred.resolve(data.payload);
                }

                requestsQueue.splice(requestIndex, 1);
            }
        });

        function DwdPluginController($element, $scope, Device, domoticzApi, deviceApi, dzNotification, dwdalarm) {
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

                // $scope.$on('device_update', function (event, deviceData) {
                //     var device = $ctrl.devices.find(function (device) {
                //         return device.idx === deviceData.idx && device.Type === deviceData.Type;
                //     });

                //     if (device) {
                //         Object.assign(device, deviceData);
                //     }
                // });
            };

            function selectPlugin(apiDeviceIdx) {
                console.log("selectPlugin: based on device idx: " + apiDeviceIdx)
                $ctrl.selectedApiDeviceIdx = apiDeviceIdx;
                dwdalarm.setControlDeviceIdx(apiDeviceIdx);

                $ctrl.controllerInfo = null;
                $ctrl.dwdDevices = null;

                // service.add(waiver)
                //     .then(function () {
                //         return service.getLast();
                //     })
                //     .then(function (result) {
                //         $scope.model.myObjects.push(result.data);
                //     });

                fetchControllerInfo(apiDeviceIdx)
                    .then(function () {
                        return fetchDwdDevices($ctrl.selectedApiPluginIdx);
                    });



                //fetchDwdDevices()
                //fetchControllerInfo()
                //    .then(fetchDwdDevices);
                //     .then(fetchZigbeeGroups);
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

                // return refreshDomoticzDevices().then(function () {
                //     $ctrl.dwdDevices = $ctrl.devices.map(function (device) {
                //         return Object.assign({
                //             model: null,
                //         }, device, {
                //             lastSeen: device.lastSeen || 'N/A',
                //             description: device.description || '',
                //             model: device.model || 'N/A',
                //             type: device.type || 'N/A'
                //         });
                //     });
                // });

                // $ctrl.dwdDevices = $ctrl.devices;

            }
            // return deviceApi.getDeviceInfo($ctrl.apiDeviceIdx).then(function (data) {
            //     $ctrl.dwdDevices = data;
            // });

            // return dwdalarm.sendRequest('devices_get').then(function (devices) {
            //     $ctrl.dwdDevices = devices.map(function (device) {
            //         return Object.assign({
            //             model: null,
            //         }, device, {
            //             lastSeen: device.lastSeen || 'N/A',
            //             description: device.description || '',
            //             model: device.model || 'N/A',
            //             type: device.type || 'N/A'
            //         });
            //     }).sort(function (a, b) {
            //         return a.friendly_name < b.friendly_name ? -1 : 1
            //     });
            // });
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
        } // DwdPluginController
    }
);
