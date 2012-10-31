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

"""Payload generator module
    Module handling generation of payload for different object types
"""

from healthnmon.resourcemodel.healthnmonResourceModel import VmHost, \
    Vm, StorageVolume, VirtualSwitch, PortGroup
from healthnmon.inventory_cache_manager import InventoryCacheManager
from string import upper
from healthnmon.constants import Constants
from healthnmon.utils import getFlagByKey
import time


def generate_payload(event_metadata, obj, **kwargs):
    """Generate payload for a event

            Parameters:
                event_metadata - EventMetaData object for this event
                obj - Resource model object for which this event is to be
                      generated
            Keyword arguments:
                additional_data - Any additional data that needs to be added
                                  for this event.
                                  This goes in the additional_data field of
                                  the message payload
                other key word arguments - This will have all the placeholder
                                           values that are to be substituted
                                           for event's long desc and short desc
            Returns:
                A dictionary having all the attributes of the payload
    """

    payloadGenerator = __factory(obj)
    return payloadGenerator.generate_payload(event_metadata, obj,
            **kwargs)


def __factory(obj):
    """Factory to create appropriate PayloadGenerator subclass object
    based on the class of the obj param

                Parameters:
                    obj - Any of the Resource model object
                Returns:
                    A PayloadGenerator or subclass object
    """

    if isinstance(obj, VmHost):
        return VmHostPayloadGenerator()
    elif isinstance(obj, Vm):
        return VmPayloadGenerator()
    elif isinstance(obj, StorageVolume):
        return StorageVolumePayloadGenerator()
    elif isinstance(obj, VirtualSwitch):
        return VirtualSwitchPayloadGenerator()
    elif isinstance(obj, PortGroup):
        return PortGroupPayloadGenerator()
    else:
        return PayloadGenerator()


def _getattr_no_none(obj, attr, default=''):
    value = getattr(obj, attr, default)
    if value is None:
        return default
    else:
        return value


class PayloadGenerator(object):

    """Base payload generator

    This will generate the generic payload attributes like entity_type,
    entity_id, name, long and short desc etc.
    It will also generate the attributes common to all types like state,
    state_desc, creation_time etc.
    If any types has a difference in generation for any of the common
    attributes then that can be re-generated in the subclass as
    subclass generation overrides this generator.
    """

    def generate_payload(
        self,
        event_metadata,
        obj,
        **kwargs
        ):
        """Generate the generic payload

            Parameters:
                event_metadata - EventMetaData object for this event
                obj - Resource model object for which this event is to be
                      generated
            Keyword arguments:
                additional_data - Any additional data that needs to be added
                                  for this event.This goes in the
                                  additional_data field of the message payload
                other key word arguments - This will have all the placeholder
                                           values that are to be substituted
                                           for event's long desc and short desc
            Returns:
                A dictionary having all the attributes of the payload
        """

        payload = {}
        payload['entity_type'] = obj.__class__.__name__
        payload['entity_id'] = _getattr_no_none(obj, 'id')
        payload['name'] = _getattr_no_none(obj, 'name')
        payload['additional_data'] = kwargs.pop('additional_data', '')
        payload['short_description'] = \
            event_metadata.get_short_desc(obj, **kwargs)
        payload['long_description'] = event_metadata.get_long_desc(obj,
                **kwargs)
        createEpoch = _getattr_no_none(obj, 'createEpoch')
        if createEpoch == '':
            payload['creation_time'] = ''
        else:
            payload['creation_time'] = time.strftime(\
             Constants.DATE_TIME_FORMAT, time.gmtime(long(createEpoch) / 1000))
        lastModifiedEpoch = _getattr_no_none(obj,
                'lastModifiedEpoch')
        if lastModifiedEpoch == '':
            payload['modified_time'] = ''
        else:
            payload['modified_time'] = time.strftime(\
             Constants.DATE_TIME_FORMAT, time.gmtime(long(lastModifiedEpoch) / 1000))
        return payload


class VmHostPayloadGenerator(PayloadGenerator):

    def _get_VmHost_state_desc(self, state):
        state_descs = \
            {Constants.VMHOST_CONNECTED: _('VmHost is in Connected state'
             ),
             Constants.VMHOST_DISCONNECTED: _('VmHost is in Disconnected state'
             )}
        if state in state_descs:
            return state_descs[state]
        else:
            return ''

    def generate_payload(
        self,
        event_metadata,
        obj,
        **kwargs
        ):
        """Generate the vmhost specific payload

            Parameters:
                event_metadata - EventMetaData object for this event
                obj - VmHost object for which this event is to be generated
            Keyword arguments:
                additional_data - Any additional data that needs to be added for this event.
                                  This goes in the additional_data field of the message payload
                other key word arguments - This will have all the placeholder values that are to be substituted for event's long desc and short desc
            Returns:
                A dictionary having all the attributes of the payload
        """

        payload = super(VmHostPayloadGenerator,
                        self).generate_payload(event_metadata, obj,
                **kwargs)

        # Add ipAddresses

        ipAddresses = []
        vmHostIpProfiles = _getattr_no_none(obj, 'ipAddresses', [])
        for ipProfile in vmHostIpProfiles:
            ipAddresses.append(ipProfile.get_ipAddress())
        payload['ipAddresses'] = ','.join(ipAddresses)

        state = _getattr_no_none(obj, 'connectionState', '')
        state_desc = self._get_VmHost_state_desc(state)
        payload['connectionState'] = state
        payload['state_description'] = state_desc

        system_model = _getattr_no_none(obj, 'model', '')
        payload['systemModel'] = system_model
        vm_ids = _getattr_no_none(obj, 'virtualMachineIds', [])
        payload['vmCount'] = len(vm_ids)
        vmHostOsProfile = _getattr_no_none(obj, 'os', None)
        if vmHostOsProfile is not None:
            payload['osVersion'] = vmHostOsProfile.get_osVersion()

        #Utilization data
        utilization_sample = {}
        utilization_data = _getattr_no_none(obj, 'utilization', None)
        if utilization_data is not None:
            memoryConsumed = utilization_data.get_totalMemory() - utilization_data.get_freeMemory()
            utilization_sample = {'cpuUserLoad': utilization_data.get_cpuUserLoad(),
                                  'processorCoresCount': utilization_data.get_ncpus(),
                                  'totalMemory': utilization_data.get_totalMemory(),
                                  'memoryConsumed': memoryConsumed,
                                 }
            payload['utilizationSampleStatus'] = utilization_data.get_status()
            payload['utilizationSample'] = utilization_sample

        total_storage_size = 0
        storage_free = 0
        storageVolumeIds = _getattr_no_none(obj, 'storageVolumeIds', [])
        for storageVolumeId in storageVolumeIds:
            storageVolume = InventoryCacheManager.get_object_from_cache(storageVolumeId,
                    Constants.StorageVolume)
            storage_pool_path = storageVolume.get_mountPoints()[0].get_path()
            if storage_pool_path == getFlagByKey('instances_path'):
                total_storage_size = long(storageVolume.get_size())
                storage_free = long(storageVolume.get_free())
                break
        payload['totalStorageSize'] = total_storage_size
        payload['storageUsed'] = total_storage_size - storage_free

        return payload


class VmPayloadGenerator(PayloadGenerator):

    def __get_vm_state_desc(self, state):
        state_descs = {
            Constants.VM_POWER_STATE_ACTIVE: _('VM is in running state'
                    ),
            Constants.VM_POWER_STATE_BUILDING: _('VM is in building state'
                    ),
            Constants.VM_POWER_STATE_REBUILDING: _('VM is in rebuilding state'
                    ),
            Constants.VM_POWER_STATE_PAUSED: _('VM is in paused state'
                    ),
            Constants.VM_POWER_STATE_SUSPENDED: _('VM is in suspended state'
                    ),
            Constants.VM_POWER_STATE_SHUTDOWN: _('VM is shutdown'),
            Constants.VM_POWER_STATE_RESCUED: _('VM is in rescued state'
                    ),
            Constants.VM_POWER_STATE_DELETED: _('VM is in deleted state'
                    ),
            Constants.VM_POWER_STATE_STOPPED: _('VM is in stopped state'
                    ),
            Constants.VM_POWER_STATE_SOFT_DELETE: _('VM underwent a soft delete'
                    ),
            Constants.VM_POWER_STATE_MIGRATING: _('VM is being migrated'
                    ),
            Constants.VM_POWER_STATE_RESIZING: _('VM is being resized'
                    ),
            Constants.VM_POWER_STATE_ERROR: _('VM is in error state'),
            Constants.VM_POWER_STATE_UNKNOWN: _('VM is in unknown state'
                    ),
            }
        #if state_descs.has_key(upper(state)):
        if upper(state) in state_descs:
            return state_descs[upper(state)]
        else:
            return ''

    def generate_payload(
        self,
        event_metadata,
        obj,
        **kwargs
        ):
        """Generate the vm specific payload

            Parameters:
                event_metadata - EventMetaData object for this event
                obj - Vm object for which this event is to be generated
            Keyword arguments:
                additional_data - Any additional data that needs to be added for this event.
                                  This goes in the additional_data field of the message payload
                other key word arguments - This will have all the placeholder values that are to be substituted for event's long desc and short desc
            Returns:
                A dictionary having all the attributes of the payload
        """

        payload = super(VmPayloadGenerator,
                        self).generate_payload(event_metadata, obj,
                **kwargs)

        # Add ipAddresses

        ipAddresses = []
        vmIpProfiles = _getattr_no_none(obj, 'ipAddresses', [])
        for ipProfile in vmIpProfiles:
            ipAddresses.append(ipProfile.get_ipAddress())
        payload['ipAddresses'] = ','.join(ipAddresses)

        # Add state and state_description

        state = _getattr_no_none(obj, 'powerState', '')
        state_desc = self.__get_vm_state_desc(state)
        payload['state'] = state
        payload['state_description'] = state_desc

        return payload


class StorageVolumePayloadGenerator(PayloadGenerator):

    def __get_storage_state_desc(self, state):
        state_descs = \
            {Constants.STORAGE_STATE_ACTIVE: _('Storage pool is active'
             ),
             Constants.STORAGE_STATE_INACTIVE: _('Storage pool is inactive'
             )}
        if state in state_descs:
            return state_descs[state]
        else:
            return ''

    def generate_payload(
        self,
        event_metadata,
        obj,
        **kwargs
        ):
        """Generate the storage specific payload

            Parameters:
                event_metadata - EventMetaData object for this event
                obj - StorageVolume object for which this event is to be generated
            Keyword arguments:
                additional_data - Any additional data that needs to be added for this event.
                                  This goes in the additional_data field of the message payload
                other key word arguments - This will have all the placeholder values that are to be substituted for event's long desc and short desc
            Returns:
                A dictionary having all the attributes of the payload
        """

        payload = super(StorageVolumePayloadGenerator,
                        self).generate_payload(event_metadata, obj,
                **kwargs)

        payload['size'] = _getattr_no_none(obj, 'size')
        payload['volumeType'] = _getattr_no_none(obj, 'volumeType')
        payload['volumeId'] = _getattr_no_none(obj, 'volumeId')

        # Add mount

        mount_points_path = []
        mount_points = _getattr_no_none(obj, 'mountPoints', [])
        for mount_point in mount_points:
            mount_points_path.append(mount_point.get_path())
        payload['mount_points'] = ','.join(mount_points_path)

        # Add state and state_description

        state = _getattr_no_none(obj, 'connectionState', '')
        state_desc = self.__get_storage_state_desc(state)
        payload['state'] = state
        payload['state_description'] = state_desc

        return payload


class VirtualSwitchPayloadGenerator(PayloadGenerator):

    def __get_virswitch_state_desc(self, state):
        state_descs = \
            {Constants.VIRSWITCH_STATE_ACTIVE: _('Virtual switch is active'
             ),
             Constants.VIRSWITCH_STATE_INACTIVE: _('Virtual switch is inactive'
             )}
        if state in state_descs:
            return state_descs[state]
        else:
            return ''

    def generate_payload(
        self,
        event_metadata,
        obj,
        **kwargs
        ):
        """Generate the virtual switch specific payload

            Parameters:
                event_metadata - EventMetaData object for this event
                obj - VirtualSwitch object for which this event is to be generated
            Keyword arguments:
                additional_data - Any additional data that needs to be added for this event.
                                  This goes in the additional_data field of the message payload
                other key word arguments - This will have all the placeholder values that are to be substituted for event's long desc and short desc
            Returns:
                A dictionary having all the attributes of the payload
        """

        payload = super(VirtualSwitchPayloadGenerator,
                        self).generate_payload(event_metadata, obj,
                **kwargs)

        payload['switchType'] = _getattr_no_none(obj, 'switchType')

        # Add networkInterfaces

        networkInterfaces = _getattr_no_none(obj, 'networkInterfaces',
                [])
        payload['networkInterfaces'] = ','.join(networkInterfaces)

        # Add state and state_description

        state = _getattr_no_none(obj, 'connectionState', '')
        state_desc = self.__get_virswitch_state_desc(state)
        payload['state'] = state
        payload['state_description'] = state_desc

        return payload


class PortGroupPayloadGenerator(PayloadGenerator):

    def generate_payload(
        self,
        event_metadata,
        obj,
        **kwargs
        ):
        """Generate the virtual switch specific payload

            Parameters:
                event_metadata - EventMetaData object for this event
                obj - PortGroup object for which this event is to be generated
            Keyword arguments:
                additional_data - Any additional data that needs to be added for this event.
                                  This goes in the additional_data field of the message payload
                other key word arguments - This will have all the placeholder values that are to be substituted for event's long desc and short desc
            Returns:
                A dictionary having all the attributes of the payload
        """

        payload = super(PortGroupPayloadGenerator,
                        self).generate_payload(event_metadata, obj,
                **kwargs)

        payload['type'] = _getattr_no_none(obj, 'type')
        payload['virtualSwitchId'] = _getattr_no_none(obj,
                'virtualSwitchId')
        return payload
