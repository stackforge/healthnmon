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

from nova import test
from healthnmon.virt.libvirt.connection import LibvirtConnection
from healthnmon.resourcemodel.healthnmonResourceModel import VmHost, Vm
from healthnmon.inventory_cache_manager import InventoryCacheManager
from healthnmon.libvirt_inventorymonitor import LibvirtVM
from healthnmon.tests import FakeLibvirt as libvirt
from healthnmon.rmcontext import ComputeRMContext
from nova.db import api as nova_db
import mox
from healthnmon.db import api
from healthnmon.constants import Constants
from nova.openstack.common.notifier import test_notifier
from healthnmon.notifier import api as notifier_api
from healthnmon.events import event_metadata


class VmEventsTest(test.TestCase):

    ''' TestCase for VM Events '''

    def _mapLibvirtvmToVm(self):
        '''Create a libvirt Domain object and map it to a healthmon
           Vm object for it
        '''

        domainObj = libvirt.virDomain()
        self.libvirtVM.domainObj = domainObj
        self.libvirtVM.domainUuid = domainObj.UUIDString()
        self.libvirtVM.Vm = Vm()
        self.libvirtVM._mapVmProperties()
        return (domainObj, self.libvirtVM.Vm)

    def _getEventMsgForEventType(self, event_type, notifications):
        '''Get the notification message corresponding to a even_type from a
           list of notifications

        Parameters:
            event_type - One of the event_metadata event_type name
            notifications - A list of notification messages
        '''

        metadata = event_metadata.get_EventMetaData(event_type)
        event_type_name = metadata.get_event_fully_qal_name()
        for msg in notifications:
            if msg['event_type'] == event_type_name:
                return msg
        return msg

    def setUp(self):
        super(VmEventsTest, self).setUp()
        self.connection = LibvirtConnection(False)
        vmHost = VmHost()
        vmHost.set_virtualMachineIds([])
        InventoryCacheManager.update_object_in_cache('1', vmHost)
        self.connection._wrapped_conn = libvirt.open('qemu:///system')
        self.libvirtVM = LibvirtVM(self.connection._wrapped_conn,
                                   '1')
        self.connection.compute_rmcontext = \
            ComputeRMContext(rmType='KVM', rmIpAddress='10.10.155.165',
                             rmUserName='openstack',
                             rmPassword='password')
        self.flags(healthnmon_notification_drivers=['nova.notifier.test_notifier']
                   )
        test_notifier.NOTIFICATIONS = []
        self.mox.StubOutWithMock(nova_db, 'service_get_all_by_topic')

        nova_db.service_get_all_by_topic(mox.IgnoreArg(),
                mox.IgnoreArg()).MultipleTimes().AndReturn(None)

    def test_vm_created_event(self):
        domainObj = libvirt.virDomain()
        self.mox.StubOutWithMock(api, 'vm_save')

        api.vm_save(mox.IgnoreArg(),
                    mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mox.StubOutWithMock(InventoryCacheManager, 'get_object_from_cache')

        InventoryCacheManager.get_object_from_cache(domainObj.UUIDString(),
                Constants.Vm).AndReturn(None)
        self.mox.ReplayAll()
        self.libvirtVM._processVm(domainObj)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 1)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = \
            event_metadata.get_EventMetaData(\
                    event_metadata.EVENT_TYPE_VM_CREATED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'Vm')
        self.assertEquals(payload['entity_id'], domainObj.UUIDString())

    def test_vm_deleted_event(self):
        self.mox.StubOutWithMock(api, 'vm_delete_by_ids')

        api.vm_delete_by_ids(mox.IgnoreArg(),
                             mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        deleted_vm_id = '25f04dd3-e924-02b2-9eac-876e3c943123'
        deleted_vm = Vm()
        deleted_vm.id = deleted_vm_id
        self.mox.StubOutWithMock(InventoryCacheManager, 'get_object_from_cache')

        InventoryCacheManager.get_object_from_cache(deleted_vm_id,
                Constants.Vm).AndReturn(deleted_vm)
        self.mox.ReplayAll()
        cachedList = ['25f04dd3-e924-02b2-9eac-876e3c943262',
                      deleted_vm_id]
        updatedList = ['25f04dd3-e924-02b2-9eac-876e3c943262']
        self.libvirtVM.processVmDeletes(cachedList, updatedList)
        self.assertTrue(len(test_notifier.NOTIFICATIONS) == 1)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertTrue(msg is not None)
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = \
            event_metadata.get_EventMetaData(\
                event_metadata.EVENT_TYPE_VM_DELETED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'Vm')
        self.assertEquals(payload['entity_id'], deleted_vm_id)

    def test_vm_reconfigured_event(self):
        mapped_tuple = self._mapLibvirtvmToVm()
        domainObj = mapped_tuple[0]
        cachedVm = mapped_tuple[1]
        cachedVm.name = 'OldName'
        self.mox.StubOutWithMock(api, 'vm_save')

        api.vm_save(mox.IgnoreArg(),
                    mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mox.StubOutWithMock(InventoryCacheManager, 'get_object_from_cache')

        InventoryCacheManager.get_object_from_cache(domainObj.UUIDString(),
                Constants.Vm).AndReturn(cachedVm)
        self.mox.ReplayAll()
        self.libvirtVM._processVm(domainObj)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 1)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = \
            event_metadata.get_EventMetaData(\
                    event_metadata.EVENT_TYPE_VM_RECONFIGURED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'Vm')
        self.assertEquals(payload['entity_id'], domainObj.UUIDString())

    def test_vm_started_event(self):
        mapped_tuple = self._mapLibvirtvmToVm()
        domainObj = mapped_tuple[0]
        cachedVm = mapped_tuple[1]
        cachedVm.powerState = Constants.VM_POWER_STATE_STOPPED
        self.mox.StubOutWithMock(api, 'vm_save')

        api.vm_save(mox.IgnoreArg(),
                    mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mox.StubOutWithMock(InventoryCacheManager, 'get_object_from_cache')

        InventoryCacheManager.get_object_from_cache(domainObj.UUIDString(),
                Constants.Vm).AndReturn(cachedVm)
        self.mox.ReplayAll()
        self.libvirtVM._processVm(domainObj)
        self.assertTrue(len(test_notifier.NOTIFICATIONS) > 0)
        msg = \
            self._getEventMsgForEventType(event_metadata.EVENT_TYPE_VM_STARTED,
                test_notifier.NOTIFICATIONS)
        self.assertTrue(msg is not None)
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = \
            event_metadata.get_EventMetaData(\
                    event_metadata.EVENT_TYPE_VM_STARTED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'Vm')
        self.assertEquals(payload['entity_id'], domainObj.UUIDString())
        self.assertEquals(payload['state'],
                          Constants.VM_POWER_STATE_ACTIVE)

    def test_vm_resumed_event(self):
        mapped_tuple = self._mapLibvirtvmToVm()
        domainObj = mapped_tuple[0]
        cachedVm = mapped_tuple[1]
        cachedVm.powerState = Constants.VM_POWER_STATE_PAUSED
        self.mox.StubOutWithMock(api, 'vm_save')

        api.vm_save(mox.IgnoreArg(),
                    mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mox.StubOutWithMock(InventoryCacheManager, 'get_object_from_cache')

        InventoryCacheManager.get_object_from_cache(domainObj.UUIDString(),
                Constants.Vm).AndReturn(cachedVm)
        self.mox.ReplayAll()
        self.libvirtVM._processVm(domainObj)
        self.assertTrue(len(test_notifier.NOTIFICATIONS) > 0)
        msg = \
            self._getEventMsgForEventType(event_metadata.EVENT_TYPE_VM_RESUMED,
                test_notifier.NOTIFICATIONS)
        self.assertTrue(msg is not None)
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = \
            event_metadata.get_EventMetaData(\
                        event_metadata.EVENT_TYPE_VM_RESUMED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'Vm')
        self.assertEquals(payload['entity_id'], domainObj.UUIDString())
        self.assertEquals(payload['state'],
                          Constants.VM_POWER_STATE_ACTIVE)

    def test_vm_shutdown_event(self):
        mapped_tuple = self._mapLibvirtvmToVm()
        domainObj = mapped_tuple[0]
        cachedVm = mapped_tuple[1]
        cachedVm.powerState = Constants.VM_POWER_STATE_ACTIVE
        self.mox.StubOutWithMock(api, 'vm_save')

        api.vm_save(mox.IgnoreArg(),
                    mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mox.StubOutWithMock(InventoryCacheManager, 'get_object_from_cache')

        InventoryCacheManager.get_object_from_cache(domainObj.UUIDString(),
                Constants.Vm).AndReturn(cachedVm)
        self.mox.StubOutWithMock(domainObj, 'state')
        domainObj.state(0).AndReturn([4])
        self.mox.ReplayAll()
        self.libvirtVM._processVm(domainObj)
        self.assertTrue(len(test_notifier.NOTIFICATIONS) > 0)
        msg = \
            self._getEventMsgForEventType(\
                        event_metadata.EVENT_TYPE_VM_SHUTDOWN,
                test_notifier.NOTIFICATIONS)
        self.assertTrue(msg is not None)
        self.assertEquals(msg['priority'], notifier_api.WARN)
        event_type = \
            event_metadata.get_EventMetaData(\
                    event_metadata.EVENT_TYPE_VM_SHUTDOWN)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'Vm')
        self.assertEquals(payload['entity_id'], domainObj.UUIDString())
        self.assertEquals(payload['state'],
                          Constants.VM_POWER_STATE_SHUTDOWN)

    def test_vm_stopped_event(self):
        mapped_tuple = self._mapLibvirtvmToVm()
        domainObj = mapped_tuple[0]
        cachedVm = mapped_tuple[1]
        cachedVm.powerState = Constants.VM_POWER_STATE_ACTIVE
        self.mox.StubOutWithMock(api, 'vm_save')

        api.vm_save(mox.IgnoreArg(),
                    mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mox.StubOutWithMock(InventoryCacheManager, 'get_object_from_cache')

        InventoryCacheManager.get_object_from_cache(domainObj.UUIDString(),
                Constants.Vm).AndReturn(cachedVm)
        self.mox.StubOutWithMock(domainObj, 'state')
        domainObj.state(0).AndReturn([5])
        self.mox.ReplayAll()
        self.libvirtVM._processVm(domainObj)
        self.assertTrue(len(test_notifier.NOTIFICATIONS) > 0)
        msg = \
            self._getEventMsgForEventType(event_metadata.EVENT_TYPE_VM_STOPPED,
                test_notifier.NOTIFICATIONS)
        self.assertTrue(msg is not None)
        self.assertEquals(msg['priority'], notifier_api.WARN)
        event_type = \
            event_metadata.get_EventMetaData(\
                    event_metadata.EVENT_TYPE_VM_STOPPED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'Vm')
        self.assertEquals(payload['entity_id'], domainObj.UUIDString())
        self.assertEquals(payload['state'],
                          Constants.VM_POWER_STATE_STOPPED)

    def test_vm_suspended_event(self):
        mapped_tuple = self._mapLibvirtvmToVm()
        domainObj = mapped_tuple[0]
        cachedVm = mapped_tuple[1]
        cachedVm.powerState = Constants.VM_POWER_STATE_ACTIVE
        self.mox.StubOutWithMock(api, 'vm_save')

        api.vm_save(mox.IgnoreArg(),
                    mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mox.StubOutWithMock(InventoryCacheManager, 'get_object_from_cache')

        InventoryCacheManager.get_object_from_cache(domainObj.UUIDString(),
                Constants.Vm).AndReturn(cachedVm)
        self.mox.StubOutWithMock(domainObj, 'state')
        domainObj.state(0).AndReturn([3])
        self.mox.ReplayAll()
        self.libvirtVM._processVm(domainObj)
        self.assertTrue(len(test_notifier.NOTIFICATIONS) > 0)
        msg = \
            self._getEventMsgForEventType(\
                event_metadata.EVENT_TYPE_VM_SUSPENDED,
                test_notifier.NOTIFICATIONS)
        self.assertTrue(msg is not None)
        self.assertEquals(msg['priority'], notifier_api.WARN)
        event_type = \
            event_metadata.get_EventMetaData(\
                        event_metadata.EVENT_TYPE_VM_SUSPENDED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'Vm')
        self.assertEquals(payload['entity_id'], domainObj.UUIDString())
        self.assertEquals(payload['state'],
                          Constants.VM_POWER_STATE_PAUSED)
