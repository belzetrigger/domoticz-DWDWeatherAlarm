define(['app', 'luxon', 'app/devices/Devices.js'], function (app, luxon) {
    var DateTime = luxon.DateTime;

    app.component('dwdDevices', {
        bindings: {
            dwdDevices: '<',
            domoticzDevices: '<',
            onUpdate: '&',
            onUpdateDomoticzDevice: '&',
        },
        templateUrl: 'app/dwd/devices.html',
        controller: DwdDevicesController
    });

    app.component('dwdDevicesTable', {
        bindings: {
            devices: '<',
            onSelect: '&',
            onUpdate: '&'
        },
        template: '<table id="dwd-devices" class="display" width="100%"></table>',
        controller: DwdDevicesTableController,
    });

    function DwdDevicesController($scope, $uibModal, dwdalarm) {
        var $ctrl = this;

        $ctrl.selectDwdDevice = selectDwdDevice;

        $ctrl.$onInit = function () {
            console.log("DwdDevicesController.onInit");
            $ctrl.associatedDevices = []
        };

        $ctrl.$onChanges = function (changes) {
            console.log("DwdDevicesController.onChanges");
            if (changes.domoticzDevices) {
                $ctrl.selectDwdDevice($ctrl.selectedDwdDevice)
            }
        };

        function selectDwdDevice(dwdDevice) {
            console.log("DwdDevicesController.selectDwdDevice");
            $ctrl.selectedDwdDevice = dwdDevice;

            if (!dwdDevice) {
                $ctrl.associatedDevices = []
            } else {
                $ctrl.associatedDevices = $ctrl.domoticzDevices
                // $ctrl.associatedDevices = $ctrl.domoticzDevices.filter(function (device) {
                //     return device.Unit > 0;
                // });
            }
        }


    }

    function DwdDevicesTableController($element, $scope, $timeout, $uibModal, dwdalarm, bootbox, dzSettings, dataTableDefaultSettings) {
        var $ctrl = this;
        var table;

        $ctrl.$onInit = function () {
            console.log("DwdDevicesTableController.onInit");
            table = $element.find('table').dataTable(Object.assign({}, dataTableDefaultSettings, {
                order: [[0, 'asc']],
                columns: [
                    { title: 'Name', data: 'name' },
                    { title: 'Data', data: 'data' },
                    { title: 'Last Seen', data: 'lastSeen', width: '150px', render: dateRenderer },
                    // {
                    //     title: '',
                    //     className: 'actions-column',
                    //     width: '80px',
                    //     data: 'ieeeAddr',
                    //     orderable: false,
                    //     render: actionsRenderer
                    // },
                ],
            }));


            table.on('select.dt', function (event, row) {
                $ctrl.onSelect({ device: row.data() });
                $scope.$apply();
            });

            table.on('deselect.dt', function () {
                //Timeout to prevent flickering when we select another item in the table
                $timeout(function () {
                    if (table.api().rows({ selected: true }).count() > 0) {
                        return;
                    }

                    $ctrl.onSelect({ device: null });
                });

                $scope.$apply();
            });

            render($ctrl.devices);
        };

        $ctrl.$onChanges = function (changes) {
            console.log("onChanges");
            if (changes.devices) {
                render($ctrl.devices);
            }
        };

        function render(items) {
            console.log("render");
            if (!table || !items) {
                return;
            }

            table.api().clear();
            table.api().rows
                .add(items)
                .draw();
        }

        function dateRenderer(data, type, row) {
            if (type === 'sort' || type === 'type' || !Number.isInteger(data)) {
                return data;
            }

            return DateTime.fromMillis(data).toFormat(dzSettings.serverDateFormat);
        }

        function actionsRenderer(data, type, row) {
            var actions = [];
            var placeholder = '<img src="../../images/empty16.png" width="16" height="16" />';

            actions.push('<button class="btn btn-icon js-check-updates" title="' + $.t('Check for OTA firmware updates') + '"><img src="images/hardware.png" /></button>');
            actions.push(placeholder)
            actions.push('<button class="btn btn-icon js-set-state" title="' + $.t('Set State') + '"><img src="images/events.png" /></button>');
            actions.push('<button class="btn btn-icon js-rename-device" title="' + $.t('Rename Device') + '"><img src="images/rename.png" /></button>');

            if (row['type'] !== 'Coordinator') {
                actions.push('<button class="btn btn-icon js-remove-device" title="' + $.t('Remove') + '"><img src="images/delete.png" /></button>');
            } else {
                actions.push(placeholder)
            }

            return actions.join('&nbsp;');
        }
    }
});
