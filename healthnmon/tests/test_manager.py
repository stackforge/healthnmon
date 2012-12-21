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
    StorageVolume, Vm, ResourceUtilization, Subnet
from healthnmon import manager
from healthnmon.profiler import helper
from healthnmon import driver
from healthnmon.inventory_cache_manager import InventoryCacheManager
from healthnmon.db import api
from healthnmon.constants import Constants
from nova.openstack.common import context
from nova import test
import mox
from nova.openstack.common import cfg
from nova.openstack.common import cfg


class HealthnMonManagerTestCase(test.TestCase):

    """Test case for scheduler manager"""

    manager_cls = manager.HealthnMonManager
    driver_cls_name = 'healthnmon.driver.Healthnmon'
    driver_cls = driver.Healthnmon

    def setUp(self):
        super(HealthnMonManagerTestCase, self).setUp()
        self.flags(healthnmon_driver=self.driver_cls_name)
        self.context = context.RequestContext('fake_user',
                                              'fake_project')

    def _createInvCache(self):
        self._createCache()
        self.mox.ReplayAll()
        self.manager = self.manager_cls()

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

    def test_1_correct_init(self):
        self._createInvCache()
        manager = self.manager
        self.assertTrue(isinstance(manager.driver, self.driver_cls))
        self.mox.UnsetStubs()

    def test_2_incorrect_init(self):
        try:
            self.manager = \
                self.manager_cls('nova.healthnmon.driver.Healthnmon1')
        except SystemExit, e:
            self.assertEquals(type(e), type(SystemExit()))
            self.assertEquals(e.code, 1)
        except Exception, e:
            self.fail('unexpected exception: %s' % e)
        else:
            self.fail('SystemExit exception expected')

        self.mox.UnsetStubs()

    def test_get_compute_list(self):
        self._createInvCache()
        expected = 'fake_computes'

        self.mox.StubOutWithMock(self.manager.driver, 'get_compute_list'
                                 )
        self.manager.driver.get_compute_list().AndReturn(expected)

        self.mox.ReplayAll()
        result = self.manager.get_compute_list()
        self.assertEqual(result, expected)
        self.mox.UnsetStubs()

    def test_poll_compute_nodes(self):
        self._createInvCache()
        self.mox.StubOutWithMock(self.manager.driver,
                                 'poll_compute_nodes')
        self.manager.driver.poll_compute_nodes(mox.IgnoreArg())

        self.mox.ReplayAll()
        self.manager._poll_compute_nodes(self.context)
        self.assertTrue(self.manager.driver.inventory_manager is not None)
        self.assertTrue(
            InventoryCacheManager.get_all_compute_inventory() is not None)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()

    def test_poll_compute_perfmon(self):
        self._createInvCache()
        self.mox.StubOutWithMock(self.manager.driver,
                                 'poll_compute_perfmon')
        self.manager.driver.poll_compute_perfmon(mox.IgnoreArg())

        self.mox.ReplayAll()
        self.manager._poll_compute_perfmon(self.context)
        self.assertTrue(
            self.manager.driver.inventory_manager.perf_green_pool is not None)
        self.assertTrue(
            InventoryCacheManager.get_all_compute_inventory() is not None)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()

    def test_get_vmhost_utilization(self):
        self._createInvCache()
        expected = ResourceUtilization()

        self.mox.StubOutWithMock(self.manager.driver,
                                 'get_resource_utilization')

        self.manager.driver.get_resource_utilization(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            Constants.VmHost,
            mox.IgnoreArg()).AndReturn(expected)

        self.mox.ReplayAll()
        result = self.manager.get_vmhost_utilization(self.context,
                                                     'uuid')
        self.assertEqual(result,
                         dict(ResourceUtilization=expected.__dict__))
        self.mox.UnsetStubs()

    def test_get_vm_utilization(self):
        self._createInvCache()
        expected = ResourceUtilization()

        self.mox.StubOutWithMock(self.manager.driver,
                                 'get_resource_utilization')

        self.manager.driver.get_resource_utilization(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            Constants.Vm,
            mox.IgnoreArg()).AndReturn(expected)

        self.mox.ReplayAll()
        result = self.manager.get_vm_utilization(self.context, 'uuid')
        self.assertEqual(result,
                         dict(ResourceUtilization=expected.__dict__))
        self.mox.UnsetStubs()

    def test_profile_cputime(self):
        self._createInvCache()
        self.mox.StubOutWithMock(helper,
                                 'profile_cputime')
        helper.profile_cputime(
            mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg())

        self.mox.ReplayAll()
        self.manager.profile_cputime(
            self.context, 'test_name', 'test_decorator', True)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()

    def test_profile_memory(self):
        self._createInvCache()
        self.mox.StubOutWithMock(helper,
                                 'profile_memory')
        helper.profile_memory(mox.IgnoreArg(
        ), mox.IgnoreArg(), mox.IgnoreArg(), mox.IgnoreArg())

        self.mox.ReplayAll()
        self.manager.profile_memory(
            self.context, 'test_name', 'test_decorator', True, True)
        self.mox.VerifyAll()
        self.mox.UnsetStubs()

    def test_log_level(self):
        self._createInvCache()
        self.mox.StubOutWithMock(helper,
                                 'setLogLevel')
        helper.setLogLevel(mox.IgnoreArg(), mox.IgnoreArg())

        self.mox.ReplayAll()
        self.manager.setLogLevel(self.context, 'DEBUG', "test_module")
        self.mox.VerifyAll()
        self.mox.UnsetStubs()

    def test_register_flag(self):
        self.mox.StubOutWithMock(cfg.CommonConfigOpts, '__getattr__')
        cfg.CommonConfigOpts.__getattr__('healthnmon_driver').\
            AndRaise(cfg.NoSuchOptError('healthnmon_driver'))
        cfg.CommonConfigOpts.__getattr__('perfmon_refresh_interval').\
            AndRaise(cfg.NoSuchOptError('perfmon_refresh_interval'))
        cfg.CommonConfigOpts.__getattr__('healthnmon_topic').\
            AndRaise(cfg.NoSuchOptError('healthnmon_topic'))
        self.mox.StubOutWithMock(cfg.CommonConfigOpts, 'register_opts')
        cfg.CommonConfigOpts.register_opts(mox.IgnoreArg()). \
            MultipleTimes().AndReturn(None)
        self.mox.ReplayAll()
        manager.register_flags()
        self.mox.UnsetStubs()
        # Note : Nothing to be asserted. Only for coverage
