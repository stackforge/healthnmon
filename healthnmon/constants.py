# vim: tabstop=4 shiftwidth=4 softtabstop=4

#          (c) Copyright 2012 Hewlett-Packard Development Company, L.P.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

""" Defines constants for healthnmon module """


class Constants(object):

    VmHost = 'VmHost'
    Vm = 'Vm'
    StorageVolume = 'StorageVolume'
    VirtualSwitch = 'VirtualSwitch'
    PortGroup = 'PortGroup'
    Network = 'Network'
    OLD_STATS = 'old_stats'
    NEW_STATS = 'new_stats'

    # Vm_Power_States

    VM_POWER_STATE_ACTIVE = 'ACTIVE'
    VM_POWER_STATE_BUILDING = 'BUILDING'
    VM_POWER_STATE_REBUILDING = 'REBUILDING'
    VM_POWER_STATE_PAUSED = 'PAUSED'
    VM_POWER_STATE_SUSPENDED = 'SUSPENDED'
    VM_POWER_STATE_SHUTDOWN = 'SHUTDOWN'
    VM_POWER_STATE_RESCUED = 'RESCUED'
    VM_POWER_STATE_DELETED = 'DELETED'
    VM_POWER_STATE_STOPPED = 'STOPPED'
    VM_POWER_STATE_SOFT_DELETE = 'SOFT_DELETE'
    VM_POWER_STATE_MIGRATING = 'MIGRATING'
    VM_POWER_STATE_RESIZING = 'RESIZING'
    VM_POWER_STATE_ERROR = 'ERROR'
    VM_POWER_STATE_UNKNOWN = 'UNKNOWN'

    VM_POWER_STATES = {
        0: VM_POWER_STATE_STOPPED,
        1: VM_POWER_STATE_ACTIVE,
        2: VM_POWER_STATE_BUILDING,
        3: VM_POWER_STATE_PAUSED,
        4: VM_POWER_STATE_SHUTDOWN,
        5: VM_POWER_STATE_STOPPED,
        6: VM_POWER_STATE_ERROR,
        7: VM_POWER_STATE_ERROR,
    }

    # StorageVolume Connection States

    STORAGE_STATE_ACTIVE = 'Active'
    STORAGE_STATE_INACTIVE = 'Inactive'

    # VMHost Connection states

    VMHOST_CONNECTED = 'Connected'
    VMHOST_DISCONNECTED = 'Disconnected'

    # VirtualSwitch Connection States

    VIRSWITCH_STATE_ACTIVE = 'Active'
    VIRSWITCH_STATE_INACTIVE = 'Inactive'

    # Date/Time fields in ISO 8601 format
    DATE_TIME_FORMAT = "%Y%m%dT%H%M%S.000Z"

    # Vm Connection State
    VM_CONNECTED = 'Connected'
    VM_DISCONNECTED = 'Disconnected'

    #Vm Auto start Enabled
    AUTO_START_ENABLED = 'AutostartEnabled'
    AUTO_START_DISABLED = 'AutoStartDisabled'


class DbConstants(object):
    ORDER_ASC = 'asc'
    ORDER_DESC = 'desc'
