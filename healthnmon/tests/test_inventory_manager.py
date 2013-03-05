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

from healthnmon.resourcemodel.healthnmonResourceModel import VmHost, \
    StorageVolume, Vm, Subnet, IpAddress
from healthnmon.inventory_manager import InventoryManager, ComputeInventory
from healthnmon.inventory_cache_manager import InventoryCacheManager
from healthnmon.events import api as event_api
from healthnmon.constants import Constants
# from healthnmon import inventory_manager
from healthnmon import rmcontext
from healthnmon.db import api
# from nova.db import api as nova_db
from healthnmon import test
from nova.openstack.common import timeutils
from nova import db
from datetime import timedelta
import eventlet
import mox


def _create_Compute(compute_id=1, compute_service=None):
    if compute_service is None:
        compute_service = dict(host='host1', created_at=timeutils.utcnow(
        ), updated_at=timeutils.utcnow(), binary='healthnmon')
    return dict(id=compute_id, hypervisor_type='fake',
                service=compute_service)


class InventoryManagerTestCase(test.TestCase):

    """Test case for Inventory manager class"""

    inv_manager_cls = InventoryManager

    def setUp(self):
        super(InventoryManagerTestCase, self).setUp()

    def _createInvCache(self):
        self._createCache()
        self.mox.ReplayAll()
        self.inv_manager = self.inv_manager_cls()

    def _createCache(self):
        self.mox.StubOutWithMock(api, 'vm_host_get_all')
        vmhost = VmHost()
        vmhost.set_id('vmhost1')
        vmhost1 = VmHost()
        vmhost1.set_id('vmhost2')
        vm = Vm()
        vm.set_id('vm1')
        vm.set_powerState(Constants.VM_POWER_STATES[1])
        vm.set_vmHostId('vmhost1')
        vm1 = Vm()
        vm1.set_id('vm2')
        vm1.set_powerState(Constants.VM_POWER_STATES[1])
        vm1.set_vmHostId('vmhost2')
        vmhost.set_virtualMachineIds(['vm1', 'vm2'])
        stPool = StorageVolume()
        stPool.set_id('stpool1')
        subNet = Subnet()
        subNet.set_id('net1')
        api.vm_host_get_all(mox.IgnoreArg()).AndReturn([vmhost,
                                                        vmhost1])
        self.mox.StubOutWithMock(api, 'vm_get_all')
        api.vm_get_all(mox.IgnoreArg()).AndReturn([vm, vm1])
        self.mox.StubOutWithMock(api, 'storage_volume_get_all')
        api.storage_volume_get_all(mox.IgnoreArg()).AndReturn([stPool])
        self.mox.StubOutWithMock(api, 'subnet_get_all')
        api.subnet_get_all(mox.IgnoreArg()).AndReturn([subNet])

    def test_update(self):
        self._createInvCache()
        im = self.inv_manager
        self.mox.StubOutWithMock(im, '_refresh_from_db')

        # self.mox.StubOutWithMock(im, '_poll_computes')

        im._refresh_from_db(mox.IgnoreArg())

        # im._poll_computes()

        self.mox.ReplayAll()
        self.assertEquals(im.update(None), None)
        self.assertTrue(im.green_pool is not None)
        self.assertTrue(im._compute_inventory is not None)
        eventlet.sleep(2)
        self.mox.VerifyAll()

        self.mox.UnsetStubs()

    def test_update_object_in_cache(self):
        ipAddress = IpAddress()
        newHost = VmHost()
        InventoryCacheManager.update_object_in_cache('uuid', ipAddress)
        InventoryCacheManager.update_object_in_cache('uuid1', newHost)
        self.mox.ReplayAll()
        eventlet.sleep(2)
        self.mox.VerifyAll()
        self.assertTrue(InventoryCacheManager.get_object_from_cache(
            'uuid', Constants.VmHost) is None)
        self.assertTrue(InventoryCacheManager.get_object_from_cache(
            'uuid1', Constants.VmHost) is not None)
        self.mox.UnsetStubs()

    def test_updateInventory(self):
        self._createInvCache()
        im = self.inv_manager
        im._updateInventory(None)
        self.mox.ReplayAll()
        eventlet.sleep(2)
        self.mox.VerifyAll()
        host = InventoryCacheManager.get_object_from_cache(
            'vmhost1', Constants.VmHost)
        self.assertTrue(InventoryCacheManager.get_object_from_cache(
            'vmhost1', Constants.VmHost) is not None)
        self.assertEquals('vmhost1', host.get_id())
        self.mox.UnsetStubs()

    def test_poll_perfmon(self):
        self._createInvCache()
        compute = _create_Compute(compute_id='vmhost1')
        service = compute['service']
        rm_context = \
            rmcontext.ComputeRMContext(rmType=compute['hypervisor_type'],
                                       rmIpAddress=service['host'],
                                       rmUserName='ubuntu164',
                                       rmPassword='password')
        InventoryCacheManager.get_all_compute_inventory()['vmhost1'] = \
            ComputeInventory(rm_context)

        InventoryCacheManager.get_all_compute_inventory()[
            'vmhost1'].get_compute_conn_driver()

        im = self.inv_manager

        self.mox.ReplayAll()
        im.poll_perfmon(None)
        self.assertTrue(im.perf_green_pool is not None)
        self.assertTrue(
            InventoryCacheManager.get_all_compute_inventory() is not None)
        eventlet.sleep(2)
        self.mox.VerifyAll()

        self.mox.UnsetStubs()

    def test_get_resource_utilization(self):
        self._createInvCache()
        compute = _create_Compute(compute_id='vmhost1')
        service = compute['service']
        rm_context = \
            rmcontext.ComputeRMContext(rmType=compute['hypervisor_type'],
                                       rmIpAddress=service['host'],
                                       rmUserName='ubuntu164',
                                       rmPassword='password')
        InventoryCacheManager.get_all_compute_inventory()['vmhost1'] = \
            ComputeInventory(rm_context)

        InventoryCacheManager.get_all_compute_inventory()[
            'vmhost1'].get_compute_conn_driver()

        im = self.inv_manager

        self.mox.ReplayAll()
        im.get_resource_utilization(None, 'vmhost1', Constants.VmHost,
                                    5)
        self.mox.VerifyAll()

        self.mox.UnsetStubs()

    def test_update_throwException(self):
        self._createInvCache()
        im = self.inv_manager
        self.mox.StubOutWithMock(im, '_refresh_from_db')

        # self.mox.StubOutWithMock(im, '_poll_computes')

        im._refresh_from_db(mox.IgnoreArg())

        # im._poll_computes()

        self.mox.StubOutWithMock(ComputeInventory, 'update_inventory')

        InventoryCacheManager.get_all_compute_inventory()[
            'compute1'].update_inventory().AndRaise(Exception)

        self.mox.ReplayAll()
        im.update(None)
        self.assertRaises(Exception, self.inv_manager_cls)
        eventlet.sleep(2)
        self.mox.VerifyAll()

        self.mox.UnsetStubs()

    def test_refresh_from_db_new(self):
        self._createInvCache()
        self.inv_manager_cls._compute_inventory = {}
        compute = _create_Compute(compute_id='compute1')
        compute['hypervisor_type'] = 'QEMU'
        self.mox.StubOutWithMock(db, 'compute_node_get_all')
        db.compute_node_get_all(mox.IgnoreArg()).AndReturn([compute])

        im = self.inv_manager
        self.assertEquals(len(im._compute_inventory), 0)

        self.mox.ReplayAll()
        im._refresh_from_db(None)
        self.mox.VerifyAll()

        self.assertEquals(
            len(InventoryCacheManager.get_all_compute_inventory()), 1)
        self.assertIn(
            'compute1', InventoryCacheManager.get_all_compute_inventory())

        self.mox.UnsetStubs()

    def test_refresh_from_db_for_service_none(self):
        self._createInvCache()
        self.inv_manager_cls._compute_inventory = {}
        compute1 = _create_Compute(compute_id='compute1')
        compute1['hypervisor_type'] = 'QEMU'
        compute2 = _create_Compute(compute_id='compute2')
        compute2['service'] = None
        self.mox.StubOutWithMock(db, 'compute_node_get_all')
        db.compute_node_get_all(
            mox.IgnoreArg()).AndReturn([compute1, compute2])

        im = self.inv_manager
        self.assertEquals(len(im._compute_inventory), 0)

        self.mox.ReplayAll()
        im._refresh_from_db(None)
        self.mox.VerifyAll()

        self.assertEquals(
            len(InventoryCacheManager.get_all_compute_inventory()), 1)
        self.assertIn(
            'compute1', InventoryCacheManager.get_all_compute_inventory())
        self.assertNotIn(
            'compute2', InventoryCacheManager.get_all_compute_inventory())

    def test_refresh_from_db_for_service_disabled_updated(self):
        self._createInvCache()
        self.inv_manager_cls._compute_inventory = {}
        compute1 = _create_Compute(compute_id='vmhost1')
        srvc = compute1['service']
        compute1['service']['binary'] = 'healthnmon'
        srvc['updated_at'] = timeutils.utcnow() - timedelta(1)
        self.mox.StubOutWithMock(db, 'compute_node_get_all')
        db.compute_node_get_all(mox.IgnoreArg()).AndReturn([compute1])

        im = self.inv_manager
        self.assertEquals(len(im._compute_inventory), 0)

        self.mox.ReplayAll()
        im._refresh_from_db(None)
        self.mox.VerifyAll()

        self.assertEquals(
            len(InventoryCacheManager.get_all_compute_inventory()), 0)
        self.assertNotIn(
            'compute1', InventoryCacheManager.get_all_compute_inventory())

    def test_refresh_from_db_for_service_disabled_created(self):
        self._createInvCache()
        self.inv_manager_cls._compute_inventory = {}
        compute1 = _create_Compute(compute_id='vmhost1')
        compute1['service']['created_at'] = timeutils.utcnow() - timedelta(1)
        compute1['service']['updated_at'] = None
        self.mox.StubOutWithMock(db, 'compute_node_get_all')
        db.compute_node_get_all(mox.IgnoreArg()).AndReturn([compute1])

        im = self.inv_manager
        self.assertEquals(len(im._compute_inventory), 0)

        self.mox.ReplayAll()
        im._refresh_from_db(None)
        self.mox.VerifyAll()

        self.assertEquals(
            len(InventoryCacheManager.get_all_compute_inventory()), 0)
        self.assertNotIn(
            'compute1', InventoryCacheManager.get_all_compute_inventory())

    def test_get_inventory_cache(self):
        self._createInvCache()
        self.assertEquals(len(InventoryCacheManager.get_inventory_cache()), 4)
        self.mox.UnsetStubs()

    def test_getObjectFromCache(self):
        self._createInvCache()
        vmhost = InventoryCacheManager.get_object_from_cache('vmhost1',
                                                             Constants.VmHost)
        self.assertNotEquals(vmhost, None)
        self.assertEquals('vmhost1', vmhost.get_id())
        self.assertTrue('vm1' in vmhost.get_virtualMachineIds())
        self.mox.UnsetStubs()

    def test_getObjectFromCacheForWrongUUid(self):
        self._createInvCache()
        vmhost = InventoryCacheManager.get_object_from_cache('vmhost3',
                                                             Constants.VmHost)
        self.assertEquals(vmhost, None)
        self.mox.UnsetStubs()

    def test_delete_object_in_cache(self):
        self._createInvCache()
        vmhost = InventoryCacheManager.get_object_from_cache('vmhost1',
                                                             Constants.VmHost)
        self.assertNotEquals(vmhost, None)
        InventoryCacheManager.delete_object_in_cache('vmhost1',
                                                     Constants.VmHost)
        vmhost = InventoryCacheManager.get_object_from_cache('vmhost1',
                                                             Constants.VmHost)
        self.assertEquals(vmhost, None)
        self.mox.UnsetStubs()

    def test_get_compute_list(self):
        self._createInvCache()
        compute = _create_Compute(compute_id='compute1')
        service = compute['service']
        rm_context = \
            rmcontext.ComputeRMContext(rmType=compute['hypervisor_type'],
                                       rmIpAddress=service['host'],
                                       rmUserName='ubuntu164',
                                       rmPassword='password')
        InventoryCacheManager.get_all_compute_inventory().clear()
        InventoryCacheManager.get_all_compute_inventory()['compute1'] = \
            ComputeInventory(rm_context)

        InventoryCacheManager.get_all_compute_inventory()[
            'compute1'].update_compute_info(rm_context, compute)
        compute_info = self.inv_manager.get_compute_list()
        self.assertEquals(compute_info[0]['hypervisor_type'], 'fake')
        self.mox.UnsetStubs()

    def test_refresh_from_db_delete_host(self):
        self._createInvCache()
        InventoryCacheManager.get_all_compute_inventory().clear()
        compute = []
        self.mox.StubOutWithMock(db, 'compute_node_get_all')
        db.compute_node_get_all(mox.IgnoreArg()).AndReturn(compute)

        im = self.inv_manager
        self.assertEquals(
            len(InventoryCacheManager.get_all_compute_inventory()), 0)

        compute = _create_Compute(compute_id='vmhost1')
        service = compute['service']
        rm_context = \
            rmcontext.ComputeRMContext(rmType=compute['hypervisor_type'],
                                       rmIpAddress=service['host'],
                                       rmUserName='ubuntu164',
                                       rmPassword='password')
        InventoryCacheManager.get_all_compute_inventory()['vmhost1'] = \
            ComputeInventory(rm_context)

        vmhost = VmHost()
        vmhost.set_id('vmhost1')
        vmhost.set_name('vmhost1')
        InventoryCacheManager.get_all_compute_inventory(
        )['vmhost1'].update_compute_info(rm_context, vmhost)

        self.mox.StubOutWithMock(api, 'vm_host_delete_by_ids')

        api.vm_host_delete_by_ids(
            mox.IgnoreArg(),
            mox.IgnoreArg()).MultipleTimes().AndReturn(None)

        self.mox.StubOutWithMock(event_api, 'notify_host_update')
        event_api.notify_host_update(mox.IgnoreArg(), mox.IgnoreArg())

        self.mox.ReplayAll()

        im._refresh_from_db(None)
        self.mox.VerifyAll()
        self.mox.stubs.UnsetAll()
        self.assertEquals(
            len(InventoryCacheManager.get_all_compute_inventory()), 0)
        self.assertTrue(InventoryCacheManager.get_all_compute_inventory(
        ).get('compute1') is None)

        self.mox.UnsetStubs()
