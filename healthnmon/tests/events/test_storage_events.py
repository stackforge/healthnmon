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

from healthnmon import test
from healthnmon.virt.libvirt.connection import LibvirtConnection
from healthnmon.resourcemodel.healthnmonResourceModel import VmHost, \
    StorageVolume
from healthnmon.inventory_manager import InventoryManager
from healthnmon.inventory_cache_manager import InventoryCacheManager
from healthnmon.libvirt_inventorymonitor import LibvirtStorageVolume, \
    LibvirtVmHost
from healthnmon.tests import FakeLibvirt as libvirt
from healthnmon.rmcontext import ComputeRMContext
from nova.db import api as nova_db
import mox
from healthnmon.db import api
from healthnmon.constants import Constants
from nova.openstack.common.notifier import test_notifier
from healthnmon.notifier import api as notifier_api
from healthnmon.events import event_metadata
from healthnmon.virt import fake


class StorageVolumeEventsTest(test.TestCase):

    ''' TestCase for Storage Events '''

    def setUp(self):
        super(StorageVolumeEventsTest, self).setUp()
        self.connection = LibvirtConnection(False)
        vmHost = VmHost()
        vmHost.set_storageVolumeIds([])
        InventoryCacheManager.update_object_in_cache('1', vmHost)
        self.connection._wrapped_conn = libvirt.open('qemu:///system')
        self.LibvirtStorageVolume = \
            LibvirtStorageVolume(self.connection._wrapped_conn, '1')
        self.LibvirtStorageVolume.vmHost = vmHost
        self.LibvirtStorageVolume.cur_total_storage_size = 0
        self.LibvirtStorageVolume.curr_storage_free = 0
        self.LibvirtStorageVolume.old_total_storage_size = 0
        self.LibvirtStorageVolume.old_storage_free = 0
        self.LibvirtStorageVolume.vmHost.set_id('1')
        self.connection.compute_rmcontext = \
            ComputeRMContext(rmType='KVM', rmIpAddress='10.10.155.165',
                             rmUserName='openstack',
                             rmPassword='password')
        self.flags(healthnmon_notification_drivers=[
            'nova.notifier.test_notifier'])
        test_notifier.NOTIFICATIONS = []
        self.mox.StubOutWithMock(nova_db, 'service_get_all_by_topic')

        nova_db.service_get_all_by_topic(
            mox.IgnoreArg(),
            mox.IgnoreArg()).MultipleTimes().AndReturn(None)

    def test_storage_added_event(self):
        storagePool = libvirt.virStoragePool()
        self.mox.StubOutWithMock(api, 'storage_volume_save')

        api.storage_volume_save(
            mox.IgnoreArg(),
            mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mox.StubOutWithMock(
            InventoryCacheManager, 'get_object_from_cache')

        InventoryCacheManager.get_object_from_cache(
            storagePool.UUIDString(),
            Constants.StorageVolume).AndReturn(None)

        self.mox.ReplayAll()
        self.LibvirtStorageVolume._processStorage(storagePool)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 1)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = \
            event_metadata.get_EventMetaData(
                event_metadata.EVENT_TYPE_STORAGE_ADDED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'StorageVolume')
        self.assertEquals(payload['entity_id'],
                          storagePool.UUIDString())

    def test_storage_deleted_event(self):
        self.mox.StubOutWithMock(api, 'storage_volume_delete_by_ids')

        api.storage_volume_delete_by_ids(
            mox.IgnoreArg(),
            mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mox.StubOutWithMock(
            InventoryCacheManager, 'get_object_from_cache')
        deleted_storage_id = '3fbfbefb-17dd-07aa-2dac-13afbedf3be3'
        deleted_storage = StorageVolume()
        deleted_storage.id = deleted_storage_id

        InventoryCacheManager.get_object_from_cache(
            deleted_storage_id,
            Constants.StorageVolume).AndReturn(deleted_storage)
        self.mox.ReplayAll()
        cachedList = [deleted_storage_id,
                      '3fbfbefb-17dd-07aa-2dac-13afbedf1234']
        updatedList = ['3fbfbefb-17dd-07aa-2dac-13afbedf1234']
        self.mox.ReplayAll()
        self.LibvirtStorageVolume.processStorageDeletes(cachedList,
                                                        updatedList)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 1)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        eventMetaData = \
            event_metadata.get_EventMetaData(
                event_metadata.EVENT_TYPE_STORAGE_DELETED)
        event_type = eventMetaData.get_event_fully_qal_name()
        self.assertEquals(msg['event_type'], event_type)
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'StorageVolume')
        self.assertEquals(payload['entity_id'], deleted_storage_id)

    def test_storage_enabled_event(self):
        storagePool = libvirt.virStoragePool()
        self.mox.StubOutWithMock(api, 'storage_volume_save')

        api.storage_volume_save(
            mox.IgnoreArg(),
            mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        cachedStorageVolume = StorageVolume()
        cachedStorageVolume.id = storagePool.UUIDString()
        cachedStorageVolume.size = 0
        cachedStorageVolume.free = 0
        cachedStorageVolume.connectionState = \
            Constants.STORAGE_STATE_INACTIVE
        self.mox.StubOutWithMock(
            InventoryCacheManager, 'get_object_from_cache')

        InventoryCacheManager.get_object_from_cache(
            storagePool.UUIDString(),
            Constants.StorageVolume).AndReturn(cachedStorageVolume)
        self.mox.ReplayAll()
        self.LibvirtStorageVolume._processStorage(storagePool)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 1)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = \
            event_metadata.get_EventMetaData(
                event_metadata.EVENT_TYPE_STORAGE_ENABLED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'StorageVolume')
        self.assertEquals(payload['entity_id'],
                          storagePool.UUIDString())
        self.assertEquals(payload['state'],
                          Constants.STORAGE_STATE_ACTIVE)

    def test_storage_disabled_event(self):
        storagePool = libvirt.virStoragePool()
        self.mox.StubOutWithMock(api, 'storage_volume_save')

        api.storage_volume_save(
            mox.IgnoreArg(),
            mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        cachedStorageVolume = StorageVolume()
        cachedStorageVolume.id = storagePool.UUIDString()
        cachedStorageVolume.size = 0
        cachedStorageVolume.free = 0
        cachedStorageVolume.connectionState = \
            Constants.STORAGE_STATE_ACTIVE
        self.mox.StubOutWithMock(
            InventoryCacheManager, 'get_object_from_cache')

        InventoryCacheManager.get_object_from_cache(
            storagePool.UUIDString(),
            Constants.StorageVolume).AndReturn(cachedStorageVolume)
        self.mox.StubOutWithMock(storagePool, 'isActive')
        storagePool.isActive().AndReturn(0)

        self.mox.ReplayAll()
        self.LibvirtStorageVolume._processStorage(storagePool)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 1)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.WARN)
        event_type = \
            event_metadata.get_EventMetaData(
                event_metadata.EVENT_TYPE_STORAGE_DISABLED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'StorageVolume')
        self.assertEquals(payload['entity_id'],
                          storagePool.UUIDString())
        self.assertEquals(payload['state'],
                          Constants.STORAGE_STATE_INACTIVE)

    def test_storage_no_state_change(self):
        storagePool = libvirt.virStoragePool()
        self.mox.StubOutWithMock(api, 'storage_volume_save')

        api.storage_volume_save(
            mox.IgnoreArg(),
            mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        cachedStorageVolume = StorageVolume()
        cachedStorageVolume.id = storagePool.UUIDString()
        cachedStorageVolume.size = 0
        cachedStorageVolume.free = 0
        cachedStorageVolume.connectionState = \
            Constants.STORAGE_STATE_ACTIVE
        self.mox.StubOutWithMock(
            InventoryCacheManager, 'get_object_from_cache')

        InventoryCacheManager.get_object_from_cache(
            storagePool.UUIDString(),
            Constants.StorageVolume).AndReturn(cachedStorageVolume)

        self.mox.ReplayAll()
        nova_db.service_get_all_by_topic(None, None)
        self.LibvirtStorageVolume._processStorage(storagePool)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 0)
