define([
    'app',
    '../templates/dwdWeatherAlarm/leaflet'
],
    function (app, leaflet) {
        //var viz = new Viz(vizRenderer);

        app.component('dwdWeatherAlarmPluginRoot', {
            templateUrl: 'app/dwdweatheralarmplugin/index.html',
            controller: DwdWeatherAlarmPluginController
        });


        app.factory('dwdWeatherAlarm', function ($q, $rootScope, domoticzApi) {
            var deviceIdx = 0;
            var requestsCount = 0;
            var requestsQueue = [];

            $rootScope.$on('device_update', function (e, device) {
                if (device.idx === deviceIdx) {
                    handleResponse(JSON.parse(device.Data))
                }
            });

            return {
                setControlDeviceIdx: setControlDeviceIdx,
                sendRequest: sendRequest,
            };

            function setControlDeviceIdx(idx) {
                deviceIdx = idx;

                domoticzApi.sendCommand('clearlightlog', {
                    idx: idx
                }).catch(function () {
                    console.log('Unable to clear log for device idx:' + idx)
                });
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

        function DwdWeatherAlarmPluginController($element, $scope, Device, domoticzApi, dzNotification, dwdWeatherAlarm) {
            var $ctrl = this;

            $ctrl.selectPlugin = selectPlugin;
            $ctrl.getVersionString = getVersionString;
            $ctrl.renderNetworkMap = renderNetworkMap;
            //$ctrl.fetchZigbeeDevices = fetchZigbeeDevices;
            //$ctrl.fetchZigbeeGroups = fetchZigbeeGroups;
            //$ctrl.togglePermitJoin = togglePermitJoin;
            $ctrl.refreshDomoticzDevices = refreshDomoticzDevices;

            $ctrl.$onInit = function () {
                $ctrl.selectedApiDeviceIdx = null;
                $ctrl.devices = [];

                refreshDomoticzDevices().then(function () {
                    $ctrl.pluginApiDevices = $ctrl.devices.filter(function (device) {
                        return device.Unit === 1
                    });

                    if ($ctrl.pluginApiDevices.length > 0) {
                        $ctrl.selectPlugin($ctrl.pluginApiDevices[0].idx);
                    }
                });

                $scope.$on('device_update', function (event, deviceData) {
                    var device = $ctrl.devices.find(function (device) {
                        return device.idx === deviceData.idx && device.Type === deviceData.Type;
                    });

                    if (device) {
                        Object.assign(device, deviceData);
                    }
                });
            };

            function selectPlugin(apiDeviceIdx) {
                $ctrl.selectedApiDeviceIdx = apiDeviceIdx;
                dwdWeatherAlarm.setControlDeviceIdx(apiDeviceIdx);

                $ctrl.controllerInfo = null;
                //$ctrl.zigbeeDevices = null;
                //$ctrl.zigbeeGroups = null;
                $ctrl.isMapLoaded = false;

                fetchControllerInfo()
                    .then(fetchZigbeeDevices)
                    .then(fetchZigbeeGroups);
            }

            function fetchZigbeeDevices() {
                return dwdWeatherAlarm.sendRequest('devices_get').then(function (devices) {
                    $ctrl.zigbeeDevices = devices.map(function (device) {
                        return Object.assign({
                            model: null,
                        }, device, {
                            lastSeen: device.lastSeen || 'N/A',
                            description: device.description || '',
                            model: device.model || 'N/A',
                            type: device.type || 'N/A'
                        });
                    }).sort(function (a, b) {
                        return a.friendly_name < b.friendly_name ? -1 : 1
                    });
                });
            }



            function getVersionString() {
                return `v.${$ctrl.controllerInfo.version} (${$ctrl.controllerInfo.coordinator.type} ${$ctrl.controllerInfo.coordinator.meta.revision})`;
            }



            function refreshDomoticzDevices() {
                return domoticzApi.sendRequest({
                    type: 'devices',
                    displayhidden: 1,
                    filter: 'all',
                    used: 'all'
                })
                    .then(domoticzApi.errorHandler)
                    .then(function (response) {
                        if (response.result !== undefined) {
                            $ctrl.devices = response.result
                                .filter(function (device) {
                                    return device.HardwareType === 'dwdWeatherAlarm'
                                })
                                .map(function (device) {
                                    return new Device(device)
                                })
                        } else {
                            $ctrl.devices = [];
                        }
                    });
            }
        }
    });
