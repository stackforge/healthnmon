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
    StorageVolume, Vm, Subnet
from healthnmon.constants import Constants
from healthnmon import driver
from healthnmon.inventory_cache_manager import InventoryCacheManager
from healthnmon.db import api
from nova.openstack.common import context
from nova import test
import mox


class HealthnMonTestCase(test.TestCase):

    """Test case for scheduler manager"""

    driver_cls = driver.Healthnmon

    def setUp(self):
        super(HealthnMonTestCase, self).setUp()
        self._createCache()
        self.mox.ReplayAll()
        self.driver = self.driver_cls()
        self.context = context.RequestContext('fake_user',
                'fake_project')

    def _createCache(self):
        self.mox.StubOutWithMock(api, 'vm_host_get_all')
        vmhost = VmHost()
        vmhost.set_id('vmhost1')
        vm = Vm()
        vm.set_id('vm1')
        stPool = StorageVolume()
        stPool.set_id('stpool1')
        subnet = Subnet()
        subnet.set_id('bridge0')
        api.vm_host_get_all(mox.IgnoreArg()).AndReturn([vmhost])
        self.mox.StubOutWithMock(api, 'vm_get_all')
        api.vm_get_all(mox.IgnoreArg()).AndReturn([vm])
        self.mox.StubOutWithMock(api, 'storage_volume_get_all')
        api.storage_volume_get_all(mox.IgnoreArg()).AndReturn([stPool])
        self.mox.StubOutWithMock(api, 'subnet_get_all')
        api.subnet_get_all(mox.IgnoreArg()).AndReturn([subnet])

    def test_get_compute_list(self):
        expected = 'fake_computes'

        self.mox.StubOutWithMock(self.driver.inventory_manager,
                                 'get_compute_list')
        self.driver.inventory_manager.get_compute_list().AndReturn(expected)

        self.mox.ReplayAll()
        result = self.driver.get_compute_list()
        self.assertEqual(result, expected)
        self.mox.UnsetStubs()

    def test__poll_compute_nodes(self):
        self.mox.StubOutWithMock(self.driver.inventory_manager, 'update'
                                 )
        self.driver.inventory_manager.update(mox.IgnoreArg())
        self.mox.ReplayAll()
        self.driver.poll_compute_nodes(self.context)
        self.assertTrue(self.driver.inventory_manager != None)
        self.assertTrue(InventoryCacheManager.get_all_compute_inventory() != None)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()

    def test_poll_compute_perfmon(self):
        self.mox.StubOutWithMock(self.driver.inventory_manager,
                                 'poll_perfmon')
        self.driver.inventory_manager.poll_perfmon(mox.IgnoreArg())

        self.mox.ReplayAll()
        self.driver.poll_compute_perfmon(self.context)
        self.assertTrue(self.driver.inventory_manager.perf_green_pool != None)
        self.assertTrue(InventoryCacheManager.get_all_compute_inventory() != None)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()

    def test_get_resource_utilization(self):
        expected = 'fake_perfdata'

        self.mox.StubOutWithMock(self.driver.inventory_manager,
                                 'get_resource_utilization')

        self.driver.inventory_manager.get_resource_utilization(mox.IgnoreArg(),
                mox.IgnoreArg(), mox.IgnoreArg(),
                mox.IgnoreArg()).AndReturn(expected)

        self.mox.ReplayAll()
        result = self.driver.get_resource_utilization(self.context,
                'uuid', Constants.VmHost, 5)
        self.assertEqual(result, expected)
        self.mox.UnsetStubs()
