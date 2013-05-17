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

from healthnmon.resourcemodel.healthnmonResourceModel import VmHost, Vm
from healthnmon.virtproxy.perfmon.libvirt_perfdata import LibvirtPerfMonitor, \
    LibvirtVmHostPerfData, LibvirtVmPerfData, SamplePerfData
from healthnmon.tests import FakeLibvirt as libvirt
from healthnmon.virtproxy.virt.libvirt.connection import LibvirtConnection
from healthnmon.virtproxy.virt.libvirt import connection
from healthnmon.constants import Constants
from healthnmon.virtproxy.perfmon.perf_stats import Stats, CPUStats
from healthnmon.virtproxy import inventory_manager
from healthnmon.tests.virtproxy.perfmon import FakeSSH
from healthnmon.rmcontext import ComputeRMContext
from healthnmon.virtproxy.inventory_cache_manager import InventoryCacheManager
from healthnmon.virtproxy.inventory_manager import ComputeInventory
from healthnmon.virtproxy.events import api as event_api
from oslo.config import cfg
import unittest
import paramiko
import mox
import time


perfmon_opts = [cfg.IntOpt('perfmon_refresh_interval', default=300,
                help='performance data refresh period.')]

CONF = cfg.CONF

try:
    CONF.perfmon_refresh_interval
except cfg.NoSuchOptError:
    CONF.register_opts(perfmon_opts)


class TestLibvirtPerfData(unittest.TestCase):

    inv_manager_cls = inventory_manager.InventoryManager
    paramiko.SSHClient = FakeSSH.SSHClient
    connection.libvirt = libvirt

    @classmethod
    def setUpClass(cls):
        cls.connection = LibvirtConnection(False)
        cls.mox = mox.Mox()
        cls.connection._wrapped_conn = libvirt.open('qemu:///system')
        cls.connection.libvirt = libvirt
        cls.vm_id = '25f04dd3-e924-02b2-9eac-876e3c943262'
        cls.vmhost_id = '1'

    def setUp(self):
        self.libvirtPerf_monitor = LibvirtPerfMonitor()
        self._createPerfCache()

    def _createPerfCache(self):

        self.libvirtPerf_monitor.perfDataCache[
            self.vm_id
        ] = {Constants.OLD_STATS: None,
             Constants.NEW_STATS: None}
        self.libvirtPerf_monitor.perfDataCache[
            self.vmhost_id
        ] = {Constants.OLD_STATS: None,
             Constants.NEW_STATS: None}

    def testDelete_perfdata_fromCache(self):
        self.assertEquals(len(self.libvirtPerf_monitor.perfDataCache),
                          2)
        self.libvirtPerf_monitor.delete_perfdata_fromCache(
            self.vm_id
        )
        self.assertEquals(len(self.libvirtPerf_monitor.perfDataCache),
                          1)

    def test_refresh_perfdata_forVm(self):
        self.libvirtVM = LibvirtVmPerfData(self.connection._wrapped_conn,
                                           self.vm_id)
        self.mox.StubOutWithMock(LibvirtVmPerfData, 'refresh_perfdata')
        self.libvirtVM.refresh_perfdata().AndReturn(None)

        self.mox.ReplayAll()

        self.libvirtPerf_monitor.refresh_perfdata(
            self.connection._wrapped_conn,
            self.vm_id,
            Constants.Vm)

        self.assert_(True)

    def test_refresh_perfdata_forHost(self):
        self.mox.StubOutWithMock(event_api, 'notify_host_update')
        event_api.notify_host_update(mox.IgnoreArg(), mox.IgnoreArg())

        self.libvirtVmHost = LibvirtVmHostPerfData(
            self.connection._wrapped_conn, self.vmhost_id)
        self.mox.StubOutWithMock(LibvirtVmHostPerfData, 'refresh_perfdata')
        self.libvirtVmHost.refresh_perfdata().AndReturn(None)

        self.mox.ReplayAll()
        self.libvirtPerf_monitor.refresh_perfdata(
            self.connection._wrapped_conn,
            self.vmhost_id,
            Constants.VmHost)
        self.assert_(True)

    def test_refresh_perfdata_NoCache(self):
        self.libvirtPerf_monitor.delete_perfdata_fromCache(
            self.vm_id
        )
        self.libvirtVmHost = LibvirtVmHostPerfData(
            self.connection._wrapped_conn, self.vmhost_id)
        self.mox.StubOutWithMock(LibvirtVmHostPerfData, 'refresh_perfdata')
        self.libvirtVmHost.refresh_perfdata().AndReturn(None)

        self.mox.ReplayAll()
        self.libvirtPerf_monitor.refresh_perfdata(
            self.connection._wrapped_conn,
            self.vm_id,
            Constants.VmHost)

    def test_get_host_resource_utilization(self):
        self.sample_perfdata = SamplePerfData()
        self.mox.StubOutWithMock(SamplePerfData, 'sample_host_perfdata')
        self.sample_perfdata.sample_host_perfdata(
            self.vmhost_id, 5).AndReturn(None)
        self.mox.ReplayAll()

        result = \
            self.libvirtPerf_monitor.get_resource_utilization(
                self.vmhost_id,
                Constants.VmHost, 5)
        self.assert_(True)

    def test_get_vm_resource_utilization(self):
        self.sample_perfdata = SamplePerfData()
        self.mox.StubOutWithMock(SamplePerfData, 'sample_vm_perfdata')
        self.sample_perfdata.sample_vm_perfdata(self.vm_id, 5).AndReturn(None)
        self.mox.ReplayAll()
        result = \
            self.libvirtPerf_monitor.get_resource_utilization(
                self.vm_id,
                Constants.Vm, 5)

        self.assert_(True)

    def createInvCache(self, vmrunning, hostconnection='Connected'):
        vmhost = VmHost()
        vmhost.set_id(self.vmhost_id)
        vmhost.set_connectionState(hostconnection)
        vm = Vm()
        vm.set_id(self.vm_id)
        if vmrunning:
            vm.set_powerState(Constants.VM_POWER_STATES[1])
        else:
            vm.set_powerState(Constants.VM_POWER_STATES[0])
        vm.set_vmHostId(self.vmhost_id)
        vmhost.set_virtualMachineIds([self.vm_id
                                      ])
        vmhost.set_processorSpeedMhz(2100)
        vmhost.set_processorCoresCount(4)
        vmhost.set_processorCount('2')
        vmhost.set_memorySize(2097152)
        vmhost.set_memoryConsumed(2097152)
        InventoryCacheManager.update_object_in_cache(self.vmhost_id, vmhost)
        InventoryCacheManager.update_object_in_cache(
            self.vm_id,
            vm)

    def tearDown(self):
        self.libvirtPerf_monitor.perfDataCache = {}
        self.mox.UnsetStubs()


class TestLibvirtVmHostPerfData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.connection = LibvirtConnection(False)
        cls.mox = mox.Mox()
        cls.connection._wrapped_conn = libvirt.open('qemu:///system')
        rm_context = ComputeRMContext(
            rmType='fake', rmIpAddress='host', rmUserName='ubuntu164',
            rmPassword='password')
        cls.connection.init_rmcontext(rm_context)
        cls.connection.libvirt = libvirt
        cls.vm_id = '25f04dd3-e924-02b2-9eac-876e3c943262'
        cls.vmhost_id = '1'

    def setUp(self):
        self.libvirtPerf_monitor = LibvirtPerfMonitor()
        self.libvirtVmHost = LibvirtVmHostPerfData(
            self.connection._wrapped_conn, self.vmhost_id)
        self._createPerfCache()

    def _createPerfCache(self):

        self.libvirtPerf_monitor.perfDataCache[
            self.vmhost_id
        ] = {Constants.OLD_STATS: None,
             Constants.NEW_STATS: None}

    def _create_compute_inventory(self):
        compute_inventory = ComputeInventory(self.connection.compute_rmcontext)
        InventoryCacheManager.get_all_compute_inventory(
        )[self.vmhost_id] = compute_inventory
        InventoryCacheManager.get_all_compute_inventory(
        )[self.vm_id] = compute_inventory

        self.mox.StubOutWithMock(ComputeInventory, 'get_compute_conn_driver')
        compute_inventory.get_compute_conn_driver().AndReturn(self.connection)
        self.mox.ReplayAll()

    def test_refresh_perfdata(self):
        for _ in xrange(2):
            self._create_compute_inventory()
            self.libvirtVmHost.refresh_perfdata()
            self.mox.UnsetStubs()

        self.assertNotEquals(self.libvirtPerf_monitor.get_perfdata_fromCache(
            self.vmhost_id, Constants.NEW_STATS), None)
        self.assertNotEquals(self.libvirtPerf_monitor.get_perfdata_fromCache(
            self.vmhost_id, Constants.OLD_STATS), None)

    def test_refresh_perfdata_cpuException(self):
        self.mox.StubOutWithMock(libvirt.virConnect,
                                 'getCPUStats')
        self.connection._wrapped_conn.getCPUStats(mox.IgnoreArg(),
                                                  mox.IgnoreArg()). \
            AndRaise(libvirt.libvirtError)

        self.mox.ReplayAll()
        self.libvirtVmHost.refresh_perfdata()

        self.assertEquals(self.libvirtPerf_monitor.get_perfdata_fromCache(
            self.vmhost_id,
                          Constants.NEW_STATS).status, -1)
        self.mox.UnsetStubs()

    def test_refresh_perfdata_memoryException(self):
        self.mox.StubOutWithMock(libvirt.virConnect,
                                 'getMemoryStats')
        self.connection._wrapped_conn.getMemoryStats(mox.IgnoreArg(),
                                                     mox.IgnoreArg()). \
            AndRaise(libvirt.libvirtError)

        self.mox.ReplayAll()
        self.libvirtVmHost.refresh_perfdata()

        self.assertEquals(self.libvirtPerf_monitor.get_perfdata_fromCache(
            self.vmhost_id,
                          Constants.NEW_STATS).status, -1)
        self.mox.UnsetStubs()

    def tearDown(self):
        self.libvirtPerf_monitor.perfDataCache = {}
        self.mox.UnsetStubs()


class TestLibvirtVmPerfData(unittest.TestCase):

    libvirt_domain_cls = libvirt.virDomain

    @classmethod
    def setUpClass(cls):
        cls.connection = LibvirtConnection(False)
        cls.mox = mox.Mox()
        cls.connection._wrapped_conn = libvirt.open('qemu:///system')
        cls.connection.libvirt = libvirt
        cls.vm_id = '25f04dd3-e924-02b2-9eac-876e3c943262'
        cls.vmhost_id = '1'

    def setUp(self):
        self.libvirtPerf_monitor = LibvirtPerfMonitor()
        self.libvirtVM = LibvirtVmPerfData(self.connection._wrapped_conn,
                                           self.vm_id)
        self._createPerfCache()

    def _createPerfCache(self):

        self.libvirtPerf_monitor.perfDataCache[
            self.vm_id
        ] = {Constants.OLD_STATS: None,
             Constants.NEW_STATS: None}

    def test_refresh_perfdata(self):
        for _ in xrange(2):
            self.libvirtVM.refresh_perfdata()

        self.assertNotEquals(self.libvirtPerf_monitor.get_perfdata_fromCache(
            self.vm_id, Constants.NEW_STATS), None)
        self.assertNotEquals(self.libvirtPerf_monitor.get_perfdata_fromCache(
            self.vm_id, Constants.OLD_STATS), None)

    def test_refresh_perfdata_notvalid(self):
        for _ in xrange(2):
            self.libvirtVM.refresh_perfdata()

        self.assertNotEquals(self.libvirtPerf_monitor.get_perfdata_fromCache(
            self.vm_id, Constants.NEW_STATS), None)
        self.assertNotEquals(self.libvirtPerf_monitor.get_perfdata_fromCache(
            self.vm_id, Constants.OLD_STATS), None)

    def test_refresh_perfdata_nonactive(self):
        self.libvirtVM = LibvirtVmPerfData(
            self.connection._wrapped_conn, 'dummy')
        self.libvirtVM.refresh_perfdata()

        self.assertEquals(
            self.libvirtPerf_monitor.
            get_perfdata_fromCache('dummy', Constants.NEW_STATS), None)

    def test_refresh_perfdata_nodomainInfo(self):
        self.libvirtVM.domainObj = \
            self.connection._wrapped_conn.lookupByUUIDString(
                self.vm_id
            )
        self.mox.StubOutWithMock(self.libvirt_domain_cls, 'info')
        self.libvirtVM.domainObj.info().AndRaise(libvirt.libvirtError)

        self.mox.ReplayAll()
        self.libvirtVM.refresh_perfdata()

        self.assertEquals(self.libvirtPerf_monitor.get_perfdata_fromCache(
            self.vm_id, Constants.NEW_STATS).status, -1)
        self.mox.UnsetStubs()

    def test_refresh_perfdata_netException(self):
        self.libvirtVM.domainObj = \
            self.connection._wrapped_conn.lookupByUUIDString(
                self.vm_id
            )
        self.mox.StubOutWithMock(self.libvirt_domain_cls,
                                 'interfaceStats')
        self.libvirtVM.domainObj.interfaceStats(mox.IgnoreArg()). \
            AndRaise(libvirt.libvirtError)

        self.mox.ReplayAll()
        self.libvirtVM.refresh_perfdata()

        self.assertEquals(self.libvirtPerf_monitor.get_perfdata_fromCache(
            self.vm_id, Constants.NEW_STATS).status, -1)
        self.mox.UnsetStubs()

    def test_refresh_perfdata_diskException(self):
        self.libvirtVM.domainObj = \
            self.connection._wrapped_conn.lookupByUUIDString(
                self.vm_id
            )
        self.mox.StubOutWithMock(self.libvirt_domain_cls, 'blockStats')
        self.libvirtVM.domainObj.blockStats(mox.IgnoreArg()). \
            AndRaise(libvirt.libvirtError)

        self.mox.ReplayAll()
        self.libvirtVM.refresh_perfdata()

        self.assertEquals(self.libvirtPerf_monitor.get_perfdata_fromCache(
            self.vm_id, Constants.NEW_STATS).status, -1)
        self.mox.UnsetStubs()

    def tearDown(self):
        self.libvirtPerf_monitor.perfDataCache = {}


class TestSamplePerfData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.connection = LibvirtConnection(False)
        cls.mox = mox.Mox()
        cls.connection._wrapped_conn = libvirt.open('qemu:///system')
        cls.connection.libvirt = libvirt
        cls.vm_id = '25f04dd3-e924-02b2-9eac-876e3c943262'
        cls.vmhost_id = '1'

    def setUp(self):
        self.libvirtPerf_monitor = LibvirtPerfMonitor()
        self._createPerfCache()
        self.sample_perfdata = SamplePerfData()

    def _createPerfCache(self):

        self.libvirtPerf_monitor.perfDataCache[
            self.vm_id
        ] = {Constants.OLD_STATS: None,
             Constants.NEW_STATS: None}
        self.libvirtPerf_monitor.perfDataCache[
            self.vmhost_id
        ] = {Constants.OLD_STATS: None,
             Constants.NEW_STATS: None}

    def test_sample_vm_perfdata(self):
        self.createInvCache(True)
        old_stats = self.createfake_oldStats()
        new_stats = self.createfake_newStats()
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vm_id,
            old_stats, new_stats)

        resource_util = \
            self.sample_perfdata.sample_vm_perfdata(
                self.vm_id,
                5)

        self.assertNotEquals(self.sample_perfdata.resource_utilization,
                             None)
        self.assertEquals(resource_util.get_status(), 0)
        self._assert(resource_util)

    def test_sample_vm_perfdata_notsampled(self):
        self.createInvCache(True)
        new_stats = self.createfake_newStats()
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vm_id,
            None, new_stats)

        resource_util = \
            self.sample_perfdata.sample_vm_perfdata(
                self.vm_id,
                5)

        self.assertEquals(resource_util.get_status(), -1)

    def test_sample_vm_perfdata_notvalid(self):
        self.createInvCache(True)
        old_stats = self.createfake_oldStats()
        new_stats = self.createfake_newStats(status=False)
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vm_id,
            old_stats, new_stats)

        resource_util = \
            self.sample_perfdata.sample_vm_perfdata(
                self.vm_id,
                5)

        self.assertEquals(resource_util.get_status(), -1)

    def test_sample_vm_perfdata_notRunning(self):
        self.createInvCache(False)
        old_stats = self.createfake_oldStats()
        new_stats = self.createfake_newStats(status=False)
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vm_id,
            old_stats, new_stats)

        resource_util = \
            self.sample_perfdata.sample_vm_perfdata(
                self.vm_id,
                5)

        self.assertEquals(resource_util.get_status(), -1)

        self.assertEquals(len(self.libvirtPerf_monitor.perfDataCache),
                          1)

    def test_sample_vm_perfdata_nochange_inperf(self):
        self.createInvCache(True)
        old_stats = self.createfake_oldStats()
        new_stats = self.createfake_newStats_nochange()
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vm_id,
            old_stats, new_stats)

        resource_util = \
            self.sample_perfdata.sample_vm_perfdata(
                self.vm_id,
                5)

        self.assertEquals(resource_util.get_status(), 0)

    def test_sample_vm_perfdata_poweroff(self):
        self.createInvCache(True)
        old_stats = self.createfake_oldStats()
        new_stats = self.createfake_newStats_nochange(poweroff=True)
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vm_id,
            old_stats, new_stats)

        resource_util = \
            self.sample_perfdata.sample_vm_perfdata(
                self.vm_id,
                5)

        self.assertEquals(resource_util.get_status(), 0)

    def test_sample_vm_perfdata_negativeStats(self):
        self.createInvCache(True)
        old_stats = self.createfake_oldStats()
        new_stats = self.createfake_newStats_nochange(stats_decrement=True)
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vm_id,
            old_stats, new_stats)

        resource_util = \
            self.sample_perfdata.sample_vm_perfdata(
                self.vm_id,
                5)

        self.assertEquals(resource_util.get_status(), 0)

    def test_sample_host_perfdata(self):
        self.createInvCache(True)
        old_stats = self.createfake_oldStats()
        new_stats = self.createfake_newStats(now=True)
        old_stats_forhost = self.createfake_oldStats_forhost()
        new_stats_forhost = self.createfake_newStats_forhost()
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vmhost_id,
            old_stats_forhost, new_stats_forhost)
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vm_id,
            old_stats, new_stats)

        resource_util = self.sample_perfdata.sample_host_perfdata(
            self.vmhost_id, 5)

        self.assertNotEquals(self.libvirtPerf_monitor.get_perfdata_fromCache(
            self.vm_id, Constants.NEW_STATS), None)
        self.assertNotEquals(self.libvirtPerf_monitor.get_perfdata_fromCache(
            self.vm_id, Constants.OLD_STATS), None)

        self.assertNotEquals(self.sample_perfdata.resource_utilization,
                             None)
        self.assertEquals(resource_util.get_status(), 0)
        self._assert(resource_util)

    def test_sample_host_perfdata_invlidStatus(self):
        self.createInvCache(True)
        old_stats = self.createfake_oldStats()
        new_stats = self.createfake_newStats()
        old_stats_forhost = self.createfake_oldStats_forhost()
        new_stats_forhost = self.createfake_newStats_forhost(False)
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vmhost_id,
            old_stats_forhost, new_stats_forhost)
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vm_id,
            old_stats, new_stats)

        resource_util = self.sample_perfdata.sample_host_perfdata(
            self.vmhost_id,
            5)

        self.assertNotEquals(self.libvirtPerf_monitor.get_perfdata_fromCache(
            self.vm_id, Constants.NEW_STATS), None)
        self.assertNotEquals(self.libvirtPerf_monitor.get_perfdata_fromCache(
            self.vm_id, Constants.OLD_STATS), None)

        self.assertNotEquals(self.sample_perfdata.resource_utilization,
                             None)
        self.assertEquals(resource_util.get_status(), 0)

    def test_sample_host_perfdata_vmnotRunning(self):
        self.createInvCache(False)
        new_stats = self.createfake_newStats()
        old_stats_forhost = self.createfake_oldStats_forhost()
        new_stats_forhost = self.createfake_newStats_forhost()
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vmhost_id,
            old_stats_forhost, new_stats_forhost)

        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vm_id,
            None, new_stats)

        resource_util = self.sample_perfdata.sample_host_perfdata(
            self.vmhost_id,
            5)

        self.assertEquals(resource_util.get_status(), 0)

    def test_sample_host_perfdata_notsampled(self):
        self.createInvCache(True)
        new_stats = self.createfake_newStats()
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vm_id,
            None, new_stats)\

        old_stats_forhost = self.createfake_oldStats_forhost()
        new_stats_forhost = self.createfake_newStats_forhost()
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vmhost_id,
            old_stats_forhost, new_stats_forhost)

        resource_util = self.sample_perfdata.sample_host_perfdata(
            self.vmhost_id,
            5)

        self.assertEquals(resource_util.get_status(), 0)

    def test_sample_hostcpu_perfdata_notsampled(self):
        self.createInvCache(True)
        new_stats_forhost = self.createfake_newStats_forhost()
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vmhost_id,
            None, new_stats_forhost)

        resource_util = \
            self.sample_perfdata.sample_host_perfdata(
                self.vmhost_id,
                5)

        self.assertEquals(resource_util.get_status(), -1)

    def test_sample_hostcpu_perfdata_notvalid(self):
        self.createInvCache(True)
        old_stats_forhost = self.createfake_oldStats_forhost()
        new_stats_forhost = self.createfake_newStats_forhost(status=False)
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vmhost_id,
            old_stats_forhost, new_stats_forhost)

        resource_util = \
            self.sample_perfdata.sample_host_perfdata(
                self.vmhost_id,
                5)

        self.assertEquals(resource_util.get_status(), -1)

    def test_sample_host_perfdata_Disconnected(self):
        self.createInvCache(True, hostconnection='Disconnected')
        new_stats = self.createfake_newStats()
        LibvirtPerfMonitor.update_perfdata_InCache(
            self.vm_id,
            None, new_stats)

        resource_util = self.sample_perfdata.sample_host_perfdata(
            self.vmhost_id,
            5)

        self.assertEquals(resource_util.get_status(), -1)

    def tearDown(self):
        self.libvirtPerf_monitor.perfDataCache = {}
        self.mox.UnsetStubs()

    def createInvCache(self, vmrunning, hostconnection='Connected'):
        vmhost = VmHost()
        vmhost.set_id(self.vmhost_id)
        vmhost.set_connectionState(hostconnection)
        vm = Vm()
        vm.set_id(self.vm_id)
        if vmrunning:
            vm.set_powerState(Constants.VM_POWER_STATES[1])
        else:
            vm.set_powerState(Constants.VM_POWER_STATES[0])
        vm.set_vmHostId(self.vmhost_id)
        vmhost.set_virtualMachineIds([self.vm_id
                                      ])
        vmhost.set_processorSpeedMhz(2100)
        vmhost.set_processorCoresCount(4)
        vmhost.set_processorCount('2')
        vmhost.set_memorySize(2097152)
        vmhost.set_memoryConsumed(2097152)
        InventoryCacheManager.update_object_in_cache(self.vmhost_id, vmhost)
        InventoryCacheManager.update_object_in_cache(
            self.vm_id,
            vm)

    def create_compute_inventory(self):
        compute_inventory = ComputeInventory(self.connection.compute_rmcontext)
        InventoryCacheManager.get_all_compute_inventory(
        )[self.vmhost_id] = compute_inventory
        InventoryCacheManager.get_all_compute_inventory(
        )[self.vm_id] = compute_inventory

        self.mox.StubOutWithMock(ComputeInventory, 'get_compute_conn_driver')
        compute_inventory.get_compute_conn_driver().AndReturn(self.connection)
        self.mox.ReplayAll()

    def _assert(self, result):
        self.assertFalse((result.get_resourceId() is None or
                         result.get_resourceId() == ''), 'Resource id is null')
        self.assertFalse((result.get_timestamp() is None), 'Timestamp is null')
        self.assertFalse(
            (result.get_granularity() is None), 'Granularity is null')
        self.assertFalse(
            (result.get_cpuUserLoad() is None), 'Cpu userLoad is null')
        self.assertFalse((result.get_cpuSystemLoad(
        ) is None), 'Cpu system load is not null')
        self.assertFalse(
            (result.get_cpuUserLoad() is None), 'Cpu userLoad is null')
        self.assertFalse(
            (result.get_hostCpuSpeed() is None), 'hostCpuSpeed is null')
        self.assertFalse(
            (result.get_hostMaxCpuSpeed() is None), 'hostMaxCpuSpeed is null')
        self.assertFalse((result.get_ncpus() is None), 'NCpus is null')
        self.assertFalse(
            (result.get_diskRead() is None), 'DiskRead userLoad is null')
        self.assertFalse(
            (result.get_diskWrite() is None), 'Disk Write userLoad is null')
        self.assertFalse((result.get_netRead() is None), 'NetRead is null')
        self.assertFalse((result.get_netWrite() is None), 'NetWrite is null')
        self.assertFalse(
            (result.get_totalMemory() is None), 'Total Memory is null')
        self.assertFalse(
            (result.get_freeMemory() is None), 'Free memory is null')
        self.assertFalse((result.get_configuredMemory(
        ) is None), 'Configured Memory is null')
        self.assert_((result.get_uptimeMinute() is None), 'uptime is not null')
        self.assert_((result.get_reservedSystemCapacity(
        ) is None), 'Reserved system capacity is not null')
        self.assert_((result.get_maximumSystemCapacity(
        ) is None), 'Maximum system capacity is not null')
        self.assert_((result.get_reservedSystemCapacity(
        ) is None), 'Reserved system capacity is not null')
        self.assert_((result.get_relativeWeight(
        ) is None), 'Relative weight is not null')
        self.assert_((result.get_reservedSystemMemory(
        ) is None), 'reserved System Memory is not null')
        self.assert_((result.get_maximumSystemMemory(
        ) is None), 'maximum System Memory is not null')
        self.assert_((result.get_memoryRelativeWeight(
        ) is None), 'Memory Relative weight is not null')
        self.assertFalse((result.get_status() is None), 'Status is null')
        self.assertNotEqual(result, None)

    def createfake_oldStats(self):
        stats = Stats()
        stats.freeMemory = 0L
        stats.totalMemory = 2097152L
        stats.timestamp = 1331372444.5931201
        stats.ncpus = 1
        stats.diskReadBytes = 226644480L
        stats.diskWriteBytes = 33723392L
        stats.netReceivedBytes = 357325L
        stats.netTransmittedBytes = 8302L
        stats.cpuStats = CPUStats()
        stats.cpuStats.cycles['user'] = 696880000000
        stats.cpuStats.cycles['system'] = 696880000000
        stats.cpuPerfTime = 1331372444.3490119
        stats.diskPerfTime = 1331372444.472137
        stats.netPerfTime = 1331372444.5922019

        return stats

    def createfake_newStats_nochange(self, poweroff=False,
                                     stats_decrement=False):
        stats = Stats()
        stats.freeMemory = 0L
        stats.totalMemory = 2097152L
        stats.timestamp = 1331372444.5931201
        stats.ncpus = 1
        if poweroff:
            stats.diskReadBytes = 0
        elif stats_decrement:
            stats.diskReadBytes = 226643380L
        else:
            stats.diskReadBytes = 226644480L
        stats.diskWriteBytes = 33723392L
        stats.netReceivedBytes = 357325L
        stats.netTransmittedBytes = 8302L
        stats.cpuStats = CPUStats()
        stats.cpuStats.cycles['user'] = 696880000000
        stats.cpuStats.cycles['system'] = 696880000000
        stats.cpuPerfTime = 1331372444.3490119
        stats.diskPerfTime = 1331372444.472137
        stats.netPerfTime = 1331372444.5922019

        return stats

    def createfake_newStats(self, now=False, status=True):
        stats = Stats()
        stats.freeMemory = 0L
        stats.totalMemory = 2097152L
        if now:
            stats.timestamp = time.time()
        else:
            stats.timestamp = 1331372625.171705
        stats.ncpus = 1
        stats.diskReadBytes = 226644480L
        stats.diskWriteBytes = 34006016L
        stats.netReceivedBytes = 362137L
        stats.netTransmittedBytes = 8302L
        stats.cpuStats = CPUStats()
        stats.cpuStats.cycles['user'] = 697480000000
        stats.cpuStats.cycles['system'] = 697480000000
        stats.cpuPerfTime = 1331372624.9259009
        stats.diskPerfTime = 1331372625.050205
        stats.netPerfTime = 1331372625.1707871
        if status:
            stats.status = 0
        else:
            stats.status = -1
        return stats

    def createfake_oldStats_forhost(self):
        stats = Stats()
        stats.freeMemory = 0L
        stats.totalMemory = 2097152L
        stats.timestamp = 1331372444.5931201
        stats.ncpus = 1
        stats.cpuStats = CPUStats()
        stats.cpuStats.cycles['user'] = 696880000000
        stats.cpuStats.cycles['system'] = 696880000000
        stats.cpuPerfTime = 1331372444.3490119

        return stats

    def createfake_newStats_forhost(self, now=False, status=True):
        stats = Stats()
        stats.freeMemory = 99982L
        stats.totalMemory = 2097152L
        if now:
            stats.timestamp = time.time()
        else:
            stats.timestamp = 1331372625.171705
        stats.ncpus = 1
        stats.cpuStats = CPUStats()
        stats.cpuStats.cycles['user'] = 697480000000
        stats.cpuStats.cycles['system'] = 697480000000
        stats.cpuPerfTime = 1331372624.9259009
        if status:
            stats.status = 0
        else:
            stats.status = -1
        return stats
