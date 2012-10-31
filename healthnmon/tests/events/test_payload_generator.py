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

"""Unit test for payload_generator module
"""

from nova import test
from healthnmon.events import payload_generator, event_metadata
from healthnmon import notifier
from healthnmon.resourcemodel.healthnmonResourceModel import Entity, \
    Vm, IpProfile, VmHost, StorageVolume, HostMountPoint
from healthnmon.inventory_cache_manager import InventoryCacheManager
from healthnmon.constants import Constants
import time


class EventMetadataTest(test.TestCase):

    """Unit test for event_metadata module
    """

    def testPayloadGenerator(self):
        metadata = event_metadata.EventMetaData('TestEvent',
                'TestCategory', 'Short Description %(name)s',
                'Long Description %(name)s', notifier.api.INFO)
        obj = Entity()
        obj.name = 'TestName'
        payload = payload_generator.generate_payload(metadata, obj)
        self.assertEquals(payload['entity_type'],
                          obj.__class__.__name__)
        self.assertEquals(payload['name'], obj.name)

    def testVmPayloadGenerator(self):
        metadata = \
            event_metadata.get_EventMetaData(\
                    event_metadata.EVENT_TYPE_VM_CREATED)
        obj = Vm()
        obj.name = 'TestVm'
        ipProfile = IpProfile()
        ipProfile.ipAddress = '10.10.10.1'
        obj.add_ipAddresses(ipProfile)
        payload = payload_generator.generate_payload(metadata, obj)
        self.assertEquals(payload['entity_type'],
                          obj.__class__.__name__)
        self.assertEquals(payload['name'], obj.name)
        self.assertEquals(payload['ipAddresses'],
                          ipProfile.ipAddress)

    def testVmHostPayloadGenerator(self):
        metadata = \
            event_metadata.get_EventMetaData(\
                event_metadata.EVENT_TYPE_HOST_ADDED)
        obj = VmHost()
        obj.name = 'TestVmHost'
        ipProfile = IpProfile()
        ipProfile.ipAddress = '10.10.10.1'
        obj.add_ipAddresses(ipProfile)
        payload = payload_generator.generate_payload(metadata, obj)
        self.assertEquals(payload['entity_type'],
                          obj.__class__.__name__)
        self.assertEquals(payload['name'], obj.name)
        self.assertEquals(payload['ipAddresses'],
                          ipProfile.ipAddress)

    def testVmHostPayload_with_storage_size(self):
        self.flags(instances_path="/var/lib/nova/instances")
        metadata = \
            event_metadata.get_EventMetaData(\
                event_metadata.EVENT_TYPE_HOST_ADDED)
        obj = VmHost()
        obj.name = 'TestVmHost'
        ipProfile = IpProfile()
        ipProfile.ipAddress = '10.10.10.1'
        obj.add_ipAddresses(ipProfile)
        storage_obj = StorageVolume()
        storage_obj.id = "storage_id"
        storage_obj.name = 'TestStorageVolume'
        storage_obj.connectionState = 'ACTIVE'
        storage_obj.size = 200
        storage_obj.free = 100
        storage_obj.volumeType = 'DIR'
        storage_obj.volumeId = 'TestVolumeId'
        storage_obj.createEpoch = long(time.time() * 1000)
        storage_obj.lastModifiedEpoch = long(time.time() * 1000)
        mount_point = HostMountPoint()
        mount_point.set_path('/var/lib/nova/instances')
        mount_point.set_vmHostId('TestVmHost')
        storage_obj.add_mountPoints(mount_point)
        obj.add_storageVolumeIds("storage_id")
        self.mox.StubOutWithMock(InventoryCacheManager, 'get_object_from_cache')
        InventoryCacheManager.get_object_from_cache(storage_obj.id,
                Constants.StorageVolume).AndReturn(storage_obj)
        self.mox.ReplayAll()
        payload = payload_generator.generate_payload(metadata, obj)
        self.assertEquals(payload['entity_type'],
                          obj.__class__.__name__)
        self.assertEquals(payload['name'], obj.name)
        self.assertEquals(payload['ipAddresses'],
                          ipProfile.ipAddress)
        self.assertEquals(payload['totalStorageSize'],
                          storage_obj.size)
        self.assertEquals(payload['storageUsed'],
                          storage_obj.free)

    def testStorageVolumePayloadGenerator(self):
        metadata = \
            event_metadata.get_EventMetaData(\
                event_metadata.EVENT_TYPE_STORAGE_ADDED)
        obj = StorageVolume()
        obj.name = 'TestStorageVolume'
        obj.connectionState = 'ACTIVE'
        obj.size = 200
        obj.volumeType = 'DIR'
        obj.volumeId = 'TestVolumeId'
        obj.createEpoch = long(time.time() * 1000)
        obj.lastModifiedEpoch = long(time.time() * 1000)
        mount_point = HostMountPoint()
        mount_point.set_path('/root/storage/1')
        mount_point.set_vmHostId('HOST1')
        obj.add_mountPoints(mount_point)
        mount_point = HostMountPoint()
        mount_point.set_path('/root/storage/2')
        mount_point.set_vmHostId('HOST2')
        obj.add_mountPoints(mount_point)
        payload = payload_generator.generate_payload(metadata, obj)
        self.assertEquals(payload['entity_type'],
                          obj.__class__.__name__)
        self.assertEquals(payload['name'], obj.name)
        self.assertEquals(payload['state'], obj.connectionState)
        self.assertTrue(obj.mountPoints[0].path
                        in payload['mount_points'])
