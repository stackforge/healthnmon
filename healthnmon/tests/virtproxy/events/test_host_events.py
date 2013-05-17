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
from healthnmon.virtproxy.virt.libvirt.connection import LibvirtConnection
from healthnmon.resourcemodel.healthnmonResourceModel import VmHost
from healthnmon.virtproxy.inventory_manager import InventoryManager, \
    ComputeInventory
from healthnmon.virtproxy.inventory_cache_manager import InventoryCacheManager
from healthnmon.virtproxy.virt.libvirt.libvirt_inventorymonitor \
    import LibvirtVmHost
from healthnmon.tests import FakeLibvirt as libvirt
from healthnmon.rmcontext import ComputeRMContext
from nova import db as nova_db
from nova.db import api as nova_db_api
import mox
from healthnmon.db import api
from healthnmon.constants import Constants
from nova.openstack.common.notifier import test_notifier
from healthnmon.notifier import api as notifier_api
from healthnmon.virtproxy.events import event_metadata
from healthnmon.virtproxy.virt.libvirt import connection
from healthnmon import rmcontext
from healthnmon.virtproxy.virt import fake
from healthnmon.virtproxy.virt.libvirt.libvirt_inventorymonitor \
    import LibvirtEvents


class VmHostEventsTest(test.TestCase):

    ''' TestCase for Host Events '''

    def __mock_service_get_all_by_topic(self):
        self.mox.StubOutWithMock(nova_db_api, 'service_get_all_by_topic')
        nova_db_api.service_get_all_by_topic(
            mox.IgnoreArg(),
            mox.IgnoreArg()).MultipleTimes().AndReturn(None)

    def setUp(self):
        super(VmHostEventsTest, self).setUp()
        self.flags(hypervisor_type="fake")
        self.connection = LibvirtConnection(False)
        vmHost = VmHost()
        vmHost.set_virtualMachineIds([])
        InventoryCacheManager.update_object_in_cache('1', vmHost)

        rm_context = ComputeRMContext(
            rmType='QEMU', rmIpAddress='10.10.155.165',
            rmUserName='openstack',
            rmPassword='password')

        InventoryCacheManager.update_object_in_cache('1', vmHost)
        InventoryCacheManager.get_all_compute_inventory()['1'] = \
            ComputeInventory(rm_context)

        self.connection._wrapped_conn = libvirt.open('qemu:///system')
        libvirtEvents = LibvirtEvents()
        self.libvirtVmHost = LibvirtVmHost(
            self.connection._wrapped_conn, '1', libvirtEvents)
        self.connection.compute_rmcontext = rm_context
        self.flags(healthnmon_notification_drivers=[
            'nova.openstack.common.notifier.test_notifier'])
        test_notifier.NOTIFICATIONS = []

    def test_load_compute_inventory(self):
        compute_service = dict(host='host2')
        compute = dict(id='compute2', hypervisor_type='fake',
                       service=compute_service)
        self.mox.StubOutWithMock(nova_db, 'compute_node_get_all')
        nova_db.compute_node_get_all(mox.IgnoreArg()).AndReturn([compute])
        self.mox.StubOutWithMock(api, 'vm_host_get_all_by_filters')
        api.vm_host_get_all_by_filters(mox.IgnoreArg(), mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg()).AndReturn([])
        self.mox.StubOutWithMock(api, 'vm_get_all_by_filters')
        api.vm_get_all_by_filters(mox.IgnoreArg(), mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg()).AndReturn([])
        self.mox.StubOutWithMock(api, 'storage_volume_get_by_ids')
        api.storage_volume_get_by_ids(mox.IgnoreArg(),
                                      mox.IgnoreArg()).AndReturn([])
        self.mox.StubOutWithMock(api, 'subnet_get_by_ids')
        api.subnet_get_by_ids(mox.IgnoreArg(),
                              mox.IgnoreArg()).AndReturn([])

        self.mox.ReplayAll()
        InventoryManager('host2')
        compute_key_lst = InventoryCacheManager.get_all_compute_inventory(
        ).keys()
        self.assertTrue(len(compute_key_lst), 2)

    def test_host_connected_event(self):
        self.__mock_service_get_all_by_topic()
        cachedHost = VmHost()
        cachedHost.id = self.libvirtVmHost.compute_id
        cachedHost.connectionState = 'Disconnected'
        self.mox.StubOutWithMock(
            InventoryCacheManager, 'get_object_from_cache')

        InventoryCacheManager.get_object_from_cache(
            self.libvirtVmHost.compute_id,
            Constants.VmHost).AndReturn(cachedHost)

        self.mox.StubOutWithMock(
            InventoryCacheManager, 'get_compute_conn_driver')

        InventoryCacheManager.get_compute_conn_driver(
            self.libvirtVmHost.compute_id,
            Constants.VmHost).AndReturn(fake.get_connection())
        self.mox.StubOutWithMock(api, 'vm_host_save')

        api.vm_host_save(mox.IgnoreArg(),
                         mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mox.StubOutWithMock(
            self.libvirtVmHost, '_get_compute_running_status')
        self.libvirtVmHost._get_compute_running_status().AndReturn(
            (True, 'host'))
        self.mox.StubOutWithMock(
            self.libvirtVmHost, '_get_network_running_status')
        self.libvirtVmHost._get_network_running_status(
            mox.IgnoreArg()).AndReturn(True)
        self.mox.ReplayAll()
        self.libvirtVmHost.processUpdates()
        self.assertEquals(self.libvirtVmHost.vmHost.get_connectionState(),
                          Constants.VMHOST_CONNECTED)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 1)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = \
            event_metadata.get_EventMetaData(
                event_metadata.EVENT_TYPE_HOST_CONNECTED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'VmHost')
        self.assertEquals(payload['entity_id'],
                          self.libvirtVmHost.compute_id)

    def test_host_added_event(self):
        self.__mock_service_get_all_by_topic()
        self.mox.StubOutWithMock(
            InventoryCacheManager, 'get_object_from_cache')

        InventoryCacheManager.get_object_from_cache(
            self.libvirtVmHost.compute_id,
            Constants.VmHost).AndReturn(None)

        self.mox.StubOutWithMock(
            InventoryCacheManager, 'get_compute_conn_driver')

        InventoryCacheManager.get_compute_conn_driver(
            self.libvirtVmHost.compute_id,
            Constants.VmHost).AndReturn(fake.get_connection())

        self.mox.StubOutWithMock(api, 'vm_host_save')

        api.vm_host_save(mox.IgnoreArg(),
                         mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mox.StubOutWithMock(
            self.libvirtVmHost, '_get_compute_running_status')
        self.libvirtVmHost._get_compute_running_status().AndReturn(
            (True, 'host'))
        self.mox.StubOutWithMock(
            self.libvirtVmHost, '_get_network_running_status')
        self.libvirtVmHost._get_network_running_status(
            mox.IgnoreArg()).AndReturn(True)
        self.mox.ReplayAll()
        self.libvirtVmHost.processUpdates()
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 1)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = \
            event_metadata.get_EventMetaData(
                event_metadata.EVENT_TYPE_HOST_ADDED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'VmHost')
        self.assertEquals(payload['entity_id'],
                          self.libvirtVmHost.compute_id)

    def test_host_disconnected_event(self):
        self.__mock_service_get_all_by_topic()
        backedUp_libvirt = connection.libvirt
        connection.libvirt = libvirt
        try:
            compute_id = '1'
            virtConnection = LibvirtConnection(False)
            vmHost = VmHost()
            vmHost.id = compute_id
            vmHost.set_virtualMachineIds([])
            InventoryCacheManager.update_object_in_cache(compute_id, vmHost)
#            virtConnection.setUuid('34353438-3934-434e-3738-313630323543'
#                                   )
            virtConnection._wrapped_conn = None
            virtConnection.compute_rmcontext = \
                ComputeRMContext(rmType='KVM',
                                 rmIpAddress='10.10.155.165',
                                 rmUserName='openstack',
                                 rmPassword='password')
            cachedHost = VmHost()
            cachedHost.id = compute_id
            cachedHost.connectionState = Constants.VMHOST_CONNECTED
            self.mox.StubOutWithMock(InventoryCacheManager,
                                     'get_object_from_cache')
            self.mox.StubOutWithMock(
                InventoryCacheManager, 'get_compute_conn_driver')

            InventoryCacheManager.get_compute_conn_driver(
                self.libvirtVmHost.compute_id,
                Constants.VmHost).AndReturn(fake.get_connection())

            InventoryCacheManager.get_object_from_cache(
                compute_id,
                Constants.VmHost).AndReturn(cachedHost)
            self.mox.StubOutWithMock(api, 'vm_host_save')

            api.vm_host_save(mox.IgnoreArg(),
                             mox.IgnoreArg()).MultipleTimes().AndReturn(None)
            self.mox.ReplayAll()
            libvirtEvents = LibvirtEvents()
            libvirtVmHost = LibvirtVmHost(
                virtConnection._wrapped_conn, compute_id, libvirtEvents)
            self.mox.StubOutWithMock(
                libvirtVmHost, '_get_compute_running_status')
            libvirtVmHost._get_compute_running_status().AndReturn(
                (True, 'host'))
            self.mox.StubOutWithMock(
                libvirtVmHost, '_get_network_running_status')
            libvirtVmHost._get_network_running_status(
                mox.IgnoreArg()).AndReturn(True)
            self.mox.ReplayAll()
            libvirtVmHost.processUpdates()
            self.assertEquals(libvirtVmHost.vmHost.get_connectionState(),
                              Constants.VMHOST_DISCONNECTED)
            self.assertEquals(len(test_notifier.NOTIFICATIONS), 1)
            msg = test_notifier.NOTIFICATIONS[0]
            self.assertEquals(msg['priority'], notifier_api.CRITICAL)
            event_type = \
                event_metadata.get_EventMetaData(
                    event_metadata.EVENT_TYPE_HOST_DISCONNECTED)
            self.assertEquals(msg['event_type'],
                              event_type.get_event_fully_qal_name())
            payload = msg['payload']
            self.assertEquals(payload['entity_type'], 'VmHost')
            self.assertEquals(payload['entity_id'],
                              libvirtVmHost.compute_id)
        finally:
            connection.libvirt = backedUp_libvirt

    def test_host_removed_event(self):
        self.__mock_service_get_all_by_topic()
        deleted_host = VmHost()
        deleted_host.set_id('compute1')
        deleted_host.set_name('compute1')
        self.mox.StubOutWithMock(api, 'vm_host_get_all_by_filters')
        api.vm_host_get_all_by_filters(mox.IgnoreArg(), mox.IgnoreArg(),
                                       mox.IgnoreArg(), mox.IgnoreArg()).\
            AndReturn([deleted_host])
        self.mox.StubOutWithMock(api, 'vm_get_all_by_filters')
        api.vm_get_all_by_filters(mox.IgnoreArg(), mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg()).AndReturn([])
        self.mox.StubOutWithMock(api, 'storage_volume_get_by_ids')
        api.storage_volume_get_by_ids(mox.IgnoreArg(),
                                      mox.IgnoreArg()).AndReturn([])
        self.mox.StubOutWithMock(api, 'subnet_get_by_ids')
        api.subnet_get_by_ids(mox.IgnoreArg(),
                              mox.IgnoreArg()).AndReturn([])

        self.mox.StubOutWithMock(api, 'vm_host_delete_by_ids')

        api.vm_host_delete_by_ids(
            mox.IgnoreArg(),
            mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mox.StubOutWithMock(
            InventoryCacheManager, 'get_compute_conn_driver')

        InventoryCacheManager.get_compute_conn_driver(
            'compute1',
            Constants.VmHost).AndReturn(fake.get_connection())
        self.mox.ReplayAll()
        rm_context = rmcontext.ComputeRMContext(rmType='fake',
                                                rmIpAddress='host1',
                                                rmUserName='ubuntu164',
                                                rmPassword='password')
        InventoryCacheManager.get_all_compute_inventory().clear()

        InventoryCacheManager.get_all_compute_inventory()['compute1'] = \
            ComputeInventory(rm_context)
        InventoryCacheManager.get_compute_inventory(
            'compute1').update_compute_info(rm_context, deleted_host)
        self.assertEquals(
            len(InventoryCacheManager.get_all_compute_inventory()), 1)
        inv_manager = InventoryManager()
        inv_manager._refresh_from_db(None)
        self.assertEquals(
            len(InventoryCacheManager.get_all_compute_inventory()), 0)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 1)
        msg = test_notifier.NOTIFICATIONS[0]
        self.assertEquals(msg['priority'], notifier_api.INFO)
        event_type = \
            event_metadata.get_EventMetaData(
                event_metadata.EVENT_TYPE_HOST_REMOVED)
        self.assertEquals(msg['event_type'],
                          event_type.get_event_fully_qal_name())
        payload = msg['payload']
        self.assertEquals(payload['entity_type'], 'VmHost')
        self.assertEquals(payload['entity_id'], deleted_host.id)

    def test_host_removed_event_none_host(self):
        deleted_host = VmHost()
        deleted_host.set_id('compute1')
        deleted_host.set_name('compute1')
        self.mox.StubOutWithMock(api, 'vm_host_get_all_by_filters')
        api.vm_host_get_all_by_filters(mox.IgnoreArg(), mox.IgnoreArg(),
                                       mox.IgnoreArg(), mox.IgnoreArg()).\
            AndReturn([deleted_host])
        self.mox.StubOutWithMock(api, 'vm_get_all_by_filters')
        api.vm_get_all_by_filters(mox.IgnoreArg(), mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg()).AndReturn([])
        self.mox.StubOutWithMock(api, 'storage_volume_get_by_ids')
        api.storage_volume_get_by_ids(mox.IgnoreArg(),
                                      mox.IgnoreArg()).AndReturn([])
        self.mox.StubOutWithMock(api, 'subnet_get_by_ids')
        api.subnet_get_by_ids(mox.IgnoreArg(),
                              mox.IgnoreArg()).AndReturn([])
        self.mox.StubOutWithMock(api, 'vm_host_delete_by_ids')

        api.vm_host_delete_by_ids(
            mox.IgnoreArg(),
            mox.IgnoreArg()).MultipleTimes().AndReturn(None)

        self.mox.StubOutWithMock(
            InventoryCacheManager, 'get_compute_conn_driver')

        InventoryCacheManager.get_compute_conn_driver(
            'compute1',
            Constants.VmHost).AndReturn(fake.get_connection())
        self.mox.ReplayAll()

        rm_context = rmcontext.ComputeRMContext(rmType='fake',
                                                rmIpAddress='host1',
                                                rmUserName='ubuntu164',
                                                rmPassword='password')
        InventoryCacheManager.get_all_compute_inventory().clear()

        InventoryCacheManager.get_all_compute_inventory()['compute1'] = \
            ComputeInventory(rm_context)
        InventoryCacheManager.get_compute_inventory(
            'compute1').update_compute_info(rm_context, deleted_host)
        self.assertEquals(
            len(InventoryCacheManager.get_all_compute_inventory()), 1)
        InventoryCacheManager.get_inventory_cache(
        )[Constants.VmHost][deleted_host.get_id()] = None

        inv_manager = InventoryManager()
        inv_manager._refresh_from_db(None)
        self.assertEquals(
            len(InventoryCacheManager.get_all_compute_inventory()), 0)
        self.assertEquals(len(test_notifier.NOTIFICATIONS), 1)
