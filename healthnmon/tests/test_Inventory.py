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

from healthnmon.constants import Constants
from healthnmon import utils as hnm_utils
from healthnmon.db import api
from healthnmon.inventory_cache_manager import InventoryCacheManager
from healthnmon.inventory_manager import ComputeInventory
from healthnmon.libvirt_inventorymonitor import LibvirtStorageVolume, \
    LibvirtVM, LibvirtVmHost, LibvirtNetwork, LibvirtInventoryMonitor
from healthnmon.utils import XMLUtils
from healthnmon.resourcemodel.healthnmonResourceModel import VmHost, \
    VirtualSwitch, Vm, IpProfile
from healthnmon.rmcontext import ComputeRMContext
from healthnmon.tests import FakeLibvirt as libvirt
from healthnmon.virt.libvirt import connection
from healthnmon.virt.libvirt.connection import LibvirtConnection
from healthnmon.events import api as event_api
from nova import flags
from nova.db import api as nova_db
from nova import db as novadb
from healthnmon.virt import fake
import mox
import unittest
from healthnmon.virt.libvirt.libvirt_event_monitor import LibvirtEvents


class test_LibvirtVM(unittest.TestCase):

    def setUp(self):
        self.connection = LibvirtConnection(False)
        self.vmHost = VmHost()
        self.vmHost.set_virtualMachineIds([])
        InventoryCacheManager.update_object_in_cache('1', self.vmHost)

        #self.connection.setUuid('34353438-3934-434e-3738-313630323543')
        self.connection._wrapped_conn = libvirt.open('qemu:///system')
        self.libvirtVM = LibvirtVM(self.connection._wrapped_conn,
                                   '1')
        self.libvirtVM.vmHost.set_id('1')
        self.connection.compute_rmcontext = \
            ComputeRMContext(rmType='QEMU', rmIpAddress='10.10.155.165',
                             rmUserName='openstack',
                             rmPassword='password')
        self.mock = mox.Mox()
        flags.FLAGS.set_override('healthnmon_notification_drivers',
                                 ['healthnmon.notifier.log_notifier'])

    def tearDown(self):
        flags.FLAGS.set_override('healthnmon_notification_drivers', None)
        self.mock.stubs.UnsetAll()

    def test_ProcessUpdates(self):
        self.mock.StubOutWithMock(api, 'vm_save')

        api.vm_save(mox.IgnoreArg(),
                    mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.StubOutWithMock(api, 'vm_delete_by_ids')

        api.vm_delete_by_ids(mox.IgnoreArg(),
                             mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.StubOutWithMock(nova_db, 'service_get_all_by_topic')

        nova_db.service_get_all_by_topic(mox.IgnoreArg(),
                mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.StubOutWithMock(InventoryCacheManager, 'get_compute_conn_driver')

        InventoryCacheManager.get_compute_conn_driver(self.libvirtVM.compute_id,
                Constants.VmHost).AndReturn(fake.get_connection())
        self.mock.ReplayAll()
        self.assertEquals(self.libvirtVM.processUpdates(), None)
        vm = InventoryCacheManager.get_object_from_cache("25f04dd3-e924-02b2-9eac-876e3c943262", Constants.Vm)
#        self.assertEquals("TestVirtMgrVM7", vm.get_name())
        self.assertEquals("1048576", str(vm.get_memorySize()))
        self.assertEquals("hd", str(vm.get_bootOrder()).strip())
        self.mock.stubs.UnsetAll()

    def test_process_updates_for_updated_VM(self):
        self.mock.StubOutWithMock(api, 'vm_save')

        api.vm_save(mox.IgnoreArg(),
                    mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.StubOutWithMock(api, 'vm_delete_by_ids')

        api.vm_delete_by_ids(mox.IgnoreArg(),
                             mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.StubOutWithMock(nova_db, 'service_get_all_by_topic')

        nova_db.service_get_all_by_topic(mox.IgnoreArg(),
                mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.StubOutWithMock(InventoryCacheManager, 'get_compute_conn_driver')

        InventoryCacheManager.get_compute_conn_driver(self.libvirtVM.compute_id,
                Constants.VmHost).AndReturn(fake.get_connection())
        self.mock.ReplayAll()
        domainObj = libvirt.virDomain()
        self.assertEquals(self.libvirtVM.process_updates_for_updated_VM(domainObj), None)
        vm = InventoryCacheManager.get_object_from_cache("25f04dd3-e924-02b2-9eac-876e3c943262", Constants.Vm)
#        self.assertEquals("TestVirtMgrVM7", vm.get_name())
        self.assertEquals("1048576", str(vm.get_memorySize()))
        self.assertEquals("hd", str(vm.get_bootOrder()).strip())
        self.mock.stubs.UnsetAll()

    def test_process_updates_for_updated_VM_exception(self):
        domainObj = libvirt.virDomain()
        self.libvirtVM.vmHost = None
        self.libvirtVM.process_updates_for_updated_VM(domainObj)
        self.assertRaises(Exception, LibvirtVM)
        self.mock.stubs.UnsetAll()
        self.mock.VerifyAll()

    def test_ProcessUpdatesException(self):
        self.mock.StubOutWithMock(api, 'vm_save')

        api.vm_save(mox.IgnoreArg(),
                    mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.StubOutWithMock(api, 'vm_delete_by_ids')

        api.vm_delete_by_ids(mox.IgnoreArg(),
                             mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.StubOutWithMock(nova_db, 'service_get_all_by_topic')

        nova_db.service_get_all_by_topic(mox.IgnoreArg(),
                mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.StubOutWithMock(InventoryCacheManager, 'get_compute_conn_driver')

        InventoryCacheManager.get_compute_conn_driver(self.libvirtVM.compute_id,
                Constants.VmHost).AndReturn(fake.get_connection())
        mock_libvirtVm = LibvirtVM(self.connection, '1')
        self.mock.StubOutWithMock(mock_libvirtVm, 'processVmDeletes')
        mock_libvirtVm.processVmDeletes([], []).AndRaise(Exception)
        self.mock.ReplayAll()
        self.assertEquals(self.libvirtVM.processUpdates(), None)
        self.assertRaises(Exception, LibvirtVM)
        self.mock.stubs.UnsetAll()

    def test_processVm(self):
        self.mock.StubOutWithMock(api, 'vm_save')

        api.vm_save(mox.IgnoreArg(),
                    mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.StubOutWithMock(nova_db, 'service_get_all_by_topic')

        nova_db.service_get_all_by_topic(mox.IgnoreArg(),
                mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.ReplayAll()
        self.assertEquals(self.libvirtVM._processVm(libvirt.virDomain()),
                          None)
        vm = InventoryCacheManager.get_object_from_cache("25f04dd3-e924-02b2-9eac-876e3c943262", Constants.Vm)
        #self.assertEquals('Disconnected', vm.get_connectionState())
#        self.assertEquals('TestVirtMgrVM7', str(vm.get_name()))
        self.assertEquals("1048576", str(vm.get_memorySize()))
        #self.assertEquals("hd", str(vm.get_bootOrder()).strip())

        self.mock.stubs.UnsetAll()

    def test_processVmForIPAddress(self):
        self.mock.StubOutWithMock(api, 'vm_save')

        api.vm_save(mox.IgnoreArg(),
                    mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.StubOutWithMock(nova_db, 'service_get_all_by_topic')

        nova_db.service_get_all_by_topic(mox.IgnoreArg(),
                mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.StubOutWithMock(InventoryCacheManager, 'get_compute_conn_driver')

        InventoryCacheManager.get_compute_conn_driver(self.libvirtVM.compute_id,
                Constants.VmHost).AndReturn(fake.get_connection())
        self.mock.ReplayAll()
        self.assertEquals(self.libvirtVM._processVm(libvirt.virDomain()),
                          None)
        self.libvirtVM.processUpdates()
        vm = InventoryCacheManager.get_object_from_cache("25f04dd3-e924-02b2-9eac-876e3c943262", Constants.Vm)
        ipProfileList = vm.get_ipAddresses()
        self.assertTrue(ipProfileList is not None)
        self.assertTrue(ipProfileList[0].get_ipAddress() == '10.1.1.19')
        self.assertTrue(ipProfileList[1].get_ipAddress() == '10.2.1.20')

    def test_processVmException(self):
        self.assertEquals(self.libvirtVM._processVm(libvirt.virStorageVol()),
                          None)

    def test_processVmDeletes(self):
        self.mock.StubOutWithMock(api, 'vm_delete_by_ids')

        api.vm_delete_by_ids(mox.IgnoreArg(),
                             mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.StubOutWithMock(nova_db, 'service_get_all_by_topic')

        nova_db.service_get_all_by_topic(mox.IgnoreArg(),
                mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.StubOutWithMock(InventoryCacheManager, 'get_object_from_cache'
                                  )
        deleted_vm_id = '25f04dd3-e924-02b2-9eac-876e3c943123'
        deleted_vm = Vm()
        deleted_vm.id = deleted_vm_id

        InventoryCacheManager.get_object_from_cache(deleted_vm_id,
                Constants.Vm).AndReturn(deleted_vm)
        self.mock.ReplayAll()
        cachedList = ['25f04dd3-e924-02b2-9eac-876e3c943262',
                      deleted_vm_id]
        updatedList = ['25f04dd3-e924-02b2-9eac-876e3c943262']
        self.assertEquals(self.libvirtVM.processVmDeletes(cachedList,
                          updatedList), None)
        self.assertTrue(deleted_vm_id not in InventoryCacheManager.get_inventory_cache().keys())
        self.mock.stubs.UnsetAll()


class test_LibvirtVmHost(unittest.TestCase):

    def setUp(self):
        self.connection = LibvirtConnection(False)
        vmHost = VmHost()
        vmHost.set_virtualMachineIds([])

        rm_context = ComputeRMContext(rmType='QEMU', rmIpAddress='10.10.155.165',
                        rmUserName='openstack',
                        rmPassword='password')

        InventoryCacheManager.update_object_in_cache('1', vmHost)
        InventoryCacheManager.get_all_compute_inventory()['1'] = \
            ComputeInventory(rm_context)

        self.connection._wrapped_conn = libvirt.open('qemu:///system')
        libvirtEvents = LibvirtEvents()
        self.libvirtVmHost = LibvirtVmHost(self.connection._wrapped_conn, '1', libvirtEvents)
        self.connection.compute_rmcontext = rm_context
        self.mock = mox.Mox()
        flags.FLAGS.set_override('healthnmon_notification_drivers',
                                 ['healthnmon.notifier.log_notifier'])

    def test_ProcessUpdates(self):
        self.mock.StubOutWithMock(api, 'vm_host_save')

        api.vm_host_save(mox.IgnoreArg(),
                         mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.ReplayAll()
        self.assertEquals(self.libvirtVmHost.processUpdates(), None)
        host = InventoryCacheManager.get_object_from_cache('1', Constants.VmHost)
        self.assertEquals('34353438-3934-434e-3738-313630323543', host.get_uuid())
        self.assertEquals('1', host.get_id())
        self.assertEquals('ubuntu164.vmm.hp.com', host.get_name())
        self.mock.stubs.UnsetAll()

    def test_ProcessUpdatesException(self):
        self.mock.StubOutWithMock(api, 'vm_host_save')

        api.vm_host_save(mox.IgnoreArg(),
                         mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        libvirtEvents = LibvirtEvents()
        mock_libvirtVmHost = LibvirtVmHost(self.connection, '1', libvirtEvents)
        self.mock.StubOutWithMock(mock_libvirtVmHost, '_mapHostProperties')
        mock_libvirtVmHost._mapHostProperties().AndRaise(Exception)
        self.mock.ReplayAll()
        self.assertEquals(self.libvirtVmHost.processUpdates(), None)
        self.assertRaises(Exception, LibvirtVmHost)
        self.mock.stubs.UnsetAll()

    def tearDown(self):
        flags.FLAGS.set_override('healthnmon_notification_drivers', None)


class test_LibvirtVmHostDisconnected(unittest.TestCase):

    connection.libvirt = libvirt

    def setUp(self):
        self.mock = mox.Mox()
        self.connection = LibvirtConnection(False)
        vmHost = VmHost()
        vmHost.set_virtualMachineIds([])
        InventoryCacheManager.update_object_in_cache('1', vmHost)
        self.connection._wrapped_conn = None
        self.connection.compute_rmcontext = \
            ComputeRMContext(rmType='fake', rmIpAddress='10.10.155.165',
                             rmUserName='openstack',
                             rmPassword='password')
        InventoryCacheManager.get_all_compute_inventory()['1'] = \
                        ComputeInventory(self.connection.compute_rmcontext)
        self.mock.StubOutWithMock(LibvirtConnection, '_connect')

        self.connection._connect(mox.IgnoreArg(),
                mox.IgnoreArg()).AndRaise(libvirt.libvirtError)
        self.mock.ReplayAll()
        self.inventoryMonitor = LibvirtInventoryMonitor()
        libvirtEvents = LibvirtEvents()
        self.libvirtVmHost = LibvirtVmHost(self.connection._wrapped_conn, '1', libvirtEvents)
        flags.FLAGS.set_override('healthnmon_notification_drivers',
                                 ['healthnmon.notifier.log_notifier'])

    def testProcessUpdatesNoOp(self):
        self.mock.StubOutWithMock(api, 'vm_host_save')

        api.vm_host_save(mox.IgnoreArg(),
                         mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.ReplayAll()
        InventoryCacheManager.delete_object_in_cache('1', Constants.VmHost)
        self.assertEquals(self.libvirtVmHost.processUpdates(), None)
        self.assertEquals(self.libvirtVmHost.vmHost, None)
        self.mock.stubs.UnsetAll()

    def testProcessUpdates(self):
        self.mock.StubOutWithMock(api, 'vm_host_save')

        api.vm_host_save(mox.IgnoreArg(),
                         mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.StubOutWithMock(InventoryCacheManager, 'get_compute_conn_driver')

        InventoryCacheManager.get_compute_conn_driver(self.libvirtVmHost.compute_id,
                Constants.VmHost).AndReturn(fake.get_connection())
        self.mock.ReplayAll()
        self.assertEquals(self.libvirtVmHost.processUpdates(), None)
        self.assertEquals(self.libvirtVmHost.vmHost.get_connectionState(),
                          'Disconnected')
        self.mock.stubs.UnsetAll()

    def testProcessUpdates_compute_stopped(self):
        vmHost = VmHost()
        vmHost.set_id('1')
        vmHost.set_connectionState(Constants.VMHOST_CONNECTED)
        InventoryCacheManager.update_object_in_cache('1', vmHost)
        self.mock.StubOutWithMock(api, 'vm_host_save')
        api.vm_host_save(mox.IgnoreArg(), mox.IgnoreArg()).MultipleTimes().AndReturn(None)

        self.mock.StubOutWithMock(InventoryCacheManager, 'get_compute_conn_driver')
        InventoryCacheManager.get_compute_conn_driver(self.libvirtVmHost.compute_id,
                Constants.VmHost).AndReturn(fake.get_connection())

        fake_computes = [{'id': '1', 'service': {'created_at':'created', 'updated_at':'updated'}}]
        self.mock.StubOutWithMock(novadb, 'compute_node_get_all')
        novadb.compute_node_get_all(mox.IgnoreArg()).AndReturn(fake_computes)

        self.mock.StubOutWithMock(hnm_utils, 'is_service_alive')
        hnm_utils.is_service_alive(mox.IgnoreArg(), mox.IgnoreArg()).AndReturn(False)

        self.mock.StubOutWithMock(event_api, 'notify_host_update')
        event_api.notify_host_update(mox.IgnoreArg(), mox.IgnoreArg()).AndReturn(None)
        self.mock.ReplayAll()

        self.assertEquals(self.libvirtVmHost.processUpdates(), None)
        self.assertEquals(self.libvirtVmHost.cachedvmHost.get_connectionState(), 'Disconnected')
        self.mock.stubs.UnsetAll()

    def testProcessUpdates_compute_stopped_exception(self):
        vmHost = VmHost()
        vmHost.set_id('1')
        vmHost.set_connectionState(Constants.VMHOST_CONNECTED)
        InventoryCacheManager.update_object_in_cache('1', vmHost)
        self.mock.StubOutWithMock(api, 'vm_host_save')
        api.vm_host_save(mox.IgnoreArg(), mox.IgnoreArg()).MultipleTimes().AndReturn(None)

        self.mock.StubOutWithMock(InventoryCacheManager, 'get_compute_conn_driver')
        InventoryCacheManager.get_compute_conn_driver(self.libvirtVmHost.compute_id,
                Constants.VmHost).AndReturn(fake.get_connection())

        fake_computes = [{'id': '1', 'service': {'created_at': 'created', 'updated_at':'updated'}}]
        self.mock.StubOutWithMock(novadb, 'compute_node_get_all')
        novadb.compute_node_get_all(mox.IgnoreArg()).AndReturn(fake_computes)

        self.mock.StubOutWithMock(hnm_utils, 'is_service_alive')
        hnm_utils.is_service_alive(mox.IgnoreArg(), mox.IgnoreArg()).AndReturn(False)

        self.mock.StubOutWithMock(event_api, 'notify_host_update')
        event_api.notify_host_update(mox.IgnoreArg(), mox.IgnoreArg()).AndRaise(Exception())
        self.mock.ReplayAll()

        self.assertEquals(self.libvirtVmHost.processUpdates(), None)
        self.mock.stubs.UnsetAll()

    def tearDown(self):
        flags.FLAGS.set_override('healthnmon_notification_drivers', None)


class test_LibvirtStorage(unittest.TestCase):

    def setUp(self):
        self.connection = LibvirtConnection(False)
        vmHost = VmHost()
        vmHost.set_storageVolumeIds([])
        InventoryCacheManager.update_object_in_cache('1', vmHost)
        self.connection._wrapped_conn = libvirt.open('qemu:///system')
        self.LibvirtStorageVolume = \
            LibvirtStorageVolume(self.connection._wrapped_conn, '1')
        self.connection.compute_rmcontext = \
            ComputeRMContext(rmType='KVM', rmIpAddress='10.10.155.165',
                             rmUserName='openstack',
                             rmPassword='password')
        self.mock = mox.Mox()

    def test_processUpdates(self):
        self.mock.StubOutWithMock(api, 'storage_volume_delete_by_ids')

        api.storage_volume_delete_by_ids(mox.IgnoreArg(),
                mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.ReplayAll()
        defaultInstancesPath = flags.FLAGS.instances_path
        flags.FLAGS.set_override('instances_path',
                                 '/var/lib/nova/instances')
        self.assertEquals(self.LibvirtStorageVolume.processUpdates(),
                          None)
        host = InventoryCacheManager.get_object_from_cache('1', Constants.VmHost)
        self.assertEquals(self.LibvirtStorageVolume._createNovaPool(),
                          None)
        storage = InventoryCacheManager.get_object_from_cache('95f7101b-892c-c388-867a-8340e5fea27x', Constants.StorageVolume)
        self.assertTrue('95f7101b-892c-c388-867a-8340e5fea27x', host.get_storageVolumeIds())
        self.assertTrue(storage != None)
        self.assertEquals('inactivePool', storage.get_name())
        flags.FLAGS.set_override('instances_path', defaultInstancesPath)
        self.mock.stubs.UnsetAll()

    def test_processUpdatesException(self):
        self.mock.StubOutWithMock(api, 'storage_volume_delete_by_ids')

        api.storage_volume_delete_by_ids(mox.IgnoreArg(),
                mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        mock_libvirtSV = LibvirtStorageVolume(self.connection, '1')
        self.mock.StubOutWithMock(mock_libvirtSV, 'processStorageDeletes')
        mock_libvirtSV.processStorageDeletes([], []).AndRaise(Exception)
        self.mock.ReplayAll()
        self.assertEquals(self.LibvirtStorageVolume.processUpdates(),
                          None)
        self.assertRaises(Exception, LibvirtStorageVolume)
        self.mock.stubs.UnsetAll()

    def test_processStorage(self):
        self.mock.StubOutWithMock(api, 'storage_volume_save')

        api.storage_volume_save(mox.IgnoreArg(),
            mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.ReplayAll()
        self.assertEquals(
         self.LibvirtStorageVolume._processStorage(libvirt.virStoragePool()),
                          None)
        host = InventoryCacheManager.get_object_from_cache('1', Constants.VmHost)
        storage = InventoryCacheManager.get_object_from_cache('95f7101b-892c-c388-867a-8340e5fea27a', Constants.StorageVolume)
        self.assertTrue('95f7101b-892c-c388-867a-8340e5fea27a', host.get_storageVolumeIds())
        self.assertTrue(storage != None)
        self.assertEquals('default', storage.get_name())
        self.assertEquals('34353438-3934-434e-3738-313630323543', storage.get_resourceManagerId())
        self.mock.stubs.UnsetAll()

    def test_processStorageDeletes(self):
        self.mock.StubOutWithMock(api, 'storage_volume_delete_by_ids')

        api.storage_volume_delete_by_ids(mox.IgnoreArg(),
                mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.ReplayAll()
        cachedList = ['3fbfbefb-17dd-07aa-2dac-13afbedf3be3',
                      '3fbfbefb-17dd-07aa-2dac-13afbedf1234',
                      '3fbfbefb-17dd-07aa-2dac-13afbedf4321']
        updatedList = ['3fbfbefb-17dd-07aa-2dac-13afbedf1234']
        self.assertEquals(
         self.LibvirtStorageVolume.processStorageDeletes(cachedList,
                          updatedList), None)
        storage = InventoryCacheManager.get_object_from_cache('3fbfbefb-17dd-07aa-2dac-13afbedf3be3', Constants.StorageVolume)
        host = InventoryCacheManager.get_object_from_cache('1', Constants.VmHost)
        self.assertTrue(storage == None)
        self.assertTrue('3fbfbefb-17dd-07aa-2dac-13afbedf1234' not in host.get_storageVolumeIds())
        self.mock.stubs.UnsetAll()

    def test_processStorageException(self):
        self.assertEquals(self.LibvirtStorageVolume._processStorage(
                          libvirt.virDomain()),
                          None)
        self.assertRaises(Exception, self.LibvirtStorageVolume)


class test_LibvirtNetwork(unittest.TestCase):

    def setUp(self):
        self.connection = LibvirtConnection(False)
        vmHost = VmHost()
        vSwitch = VirtualSwitch()
        vSwitch.set_id('52:54:00:34:14:AE')
        vSwitch.set_name('default')
        vSwitch.set_switchType('nat')
        vmHost.set_virtualSwitches([vSwitch])
        InventoryCacheManager.update_object_in_cache('1', vmHost)
        #self.connection.setUuid('34353438-3934-434e-3738-313630323543')
        self.connection._wrapped_conn = libvirt.open('qemu:///system')
        self.connection.compute_rmcontext = \
            ComputeRMContext(rmType='KVM', rmIpAddress='10.10.155.165',
                             rmUserName='openstack',
                             rmPassword='password')
        self.LibvirtNetwork = LibvirtNetwork(self.connection, '1')
        self.mock = mox.Mox()
        flags.FLAGS.set_override('healthnmon_notification_drivers',
                                 ['healthnmon.notifier.log_notifier'])

    def test_processUpdates(self):
        self.mock.StubOutWithMock(api, 'vm_host_save')
        self.mock.StubOutWithMock(api, 'subnet_delete_by_ids')
        self.mock.StubOutWithMock(api, 'subnet_save')

        api.vm_host_save(mox.IgnoreArg(),
                         mox.IgnoreArg()).MultipleTimes().AndReturn(None)

        api.subnet_delete_by_ids(mox.IgnoreArg(),
            mox.IgnoreArg()).MultipleTimes().AndReturn(None)

        api.subnet_save(mox.IgnoreArg(),
                        mox.IgnoreArg()).MultipleTimes().AndReturn(None)

        self.mock.ReplayAll()
        self.assertEquals(self.LibvirtNetwork.processUpdates(), None)
        host = InventoryCacheManager.get_object_from_cache('1', Constants.VmHost)
        self.assertEquals('52:54:00:34:14:AE', host.get_virtualSwitches()[0].get_id())
        self.assertEquals('nat', host.get_virtualSwitches()[0].get_switchType())
        self.assertEquals('default', host.get_virtualSwitches()[0].get_name())

        self.mock.stubs.UnsetAll()

    def test_processUpdatesException(self):
        self.mock.StubOutWithMock(api, 'vm_host_save')
        self.mock.StubOutWithMock(api, 'subnet_delete_by_ids')
        self.mock.StubOutWithMock(api, 'subnet_save')

        api.vm_host_save(mox.IgnoreArg(),
                         mox.IgnoreArg()).MultipleTimes().AndReturn(None)

        api.subnet_delete_by_ids(mox.IgnoreArg(),
            mox.IgnoreArg()).MultipleTimes().AndReturn(None)

        api.subnet_save(mox.IgnoreArg(),
                        mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        mock_libvirtNetwork = LibvirtNetwork(self.connection, '1')
        self.mock.StubOutWithMock(mock_libvirtNetwork, '_processNetworkDeletes')
        mock_libvirtNetwork._processNetworkDeletes([], [],).AndRaise(Exception)
        self.mock.ReplayAll()
        self.assertEquals(self.LibvirtNetwork.processUpdates(), None)
        self.assertRaises(Exception, LibvirtNetwork)
        self.mock.stubs.UnsetAll()

    def testProcessNetworkInterface(self):
        self.mock.StubOutWithMock(api, 'subnet_delete_by_ids')

        api.subnet_delete_by_ids(mox.IgnoreArg(),
                mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.ReplayAll()
        self.assertEquals(self.LibvirtNetwork._processNetworkInterface(
                                    libvirt.virLibvirtInterfaceEth0()),
                                    None)
        host = InventoryCacheManager.get_object_from_cache('1', Constants.VmHost)
        self.assertTrue(host.get_ipAddresses != None)
        self.mock.stubs.UnsetAll()

    def testProcessNetwork(self):
        self.mock.StubOutWithMock(api, 'subnet_save')

        api.subnet_save(mox.IgnoreArg(),
                        mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.ReplayAll()
        self.assertEquals(self.LibvirtNetwork._processVirtualNetwork(
                                    libvirt.virLibvirtNetwork()),
                                    None)
        subnet = InventoryCacheManager.get_object_from_cache('Subnet_52:54:00:34:14:AE', Constants.Network)
        self.assertTrue(subnet != None)
        self.assertFalse(subnet.get_isBootNetwork())
        self.assertEquals('default', subnet.get_name())
        self.mock.stubs.UnsetAll()

    def testProcessnetworkDeletes(self):
        self.mock.StubOutWithMock(api, 'subnet_delete_by_ids')

        api.subnet_delete_by_ids(mox.IgnoreArg(),
                mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.ReplayAll()
#        cachedSwitchList = ['52:54:00:34:14:AC',
#                            '52:54:00:34:14:AB',
#                            '52:54:00:34:14:AE']
#        updatedSwitchList = ['52:54:00:34:14:AE']
        cachedSubnetList = \
            ['Subnet_52:54:00:34:14:AF',
             'Subnet_52:54:00:34:14:AG',
             'Subnet_52:54:00:34:14:AE']
        updatedSubnetList = \
            ['Subnet_52:54:00:34:14:AE']
        self.assertEquals(self.LibvirtNetwork._processNetworkDeletes(
                          cachedSubnetList,
                          updatedSubnetList), None)
        subnet = InventoryCacheManager.get_object_from_cache('Subnet_52:54:00:34:14:AE', Constants.Network)
        self.assertTrue(subnet != None)
        subnet = InventoryCacheManager.get_object_from_cache('Subnet_52:54:00:34:14:AG', Constants.Network)
        self.assertTrue(subnet is None)
        self.mock.stubs.UnsetAll()

    def testGetIpType(self):
        self.assertEquals(self.LibvirtNetwork._getIpType('10.10.155.63'
                          ), 'IPV4')
        self.assertEquals(self.LibvirtNetwork._getIpType('g3:1d:1a:63:5e:a3'
                          ), 'IPV6')
        self.assertEquals(self.LibvirtNetwork._getIpType(''),
                          'UNSPECIFIED')
        self.mock.stubs.UnsetAll()


class test_LibvirtInventoryMonitor(unittest.TestCase):

    connection.libvirt = libvirt

    def setUp(self):
        self.mock = mox.Mox()
        self.connection = LibvirtConnection(False)
        self.connection._wrapped_conn = libvirt.open('qemu:///system')
        vmHost = VmHost()
        InventoryCacheManager.update_object_in_cache('1', vmHost)
        self.connection.compute_rmcontext = \
            ComputeRMContext(rmType='fake', rmIpAddress='10.10.155.165',
                             rmUserName='openstack',
                             rmPassword='password')
        InventoryCacheManager.get_all_compute_inventory()['1'] = \
                        ComputeInventory(self.connection.compute_rmcontext)
        self.mock.StubOutWithMock(LibvirtConnection, '_connect')

        self.connection._connect(mox.IgnoreArg(),
                mox.IgnoreArg()).AndRaise(libvirt.libvirtError)
        self.mock.ReplayAll()
        self.inventoryMonitor = LibvirtInventoryMonitor()
#        self.libvirtVmHost = LibvirtVmHost(self.connection, '1')
        flags.FLAGS.set_override('healthnmon_notification_drivers',
                                 ['healthnmon.notifier.log_notifier'])
        self.libvirtInventoryMonitor = LibvirtInventoryMonitor()

    def test_collectInventory(self):
        self.mock.StubOutWithMock(api, 'vm_host_save')
        api.vm_host_save(mox.IgnoreArg(),
                         mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mock.ReplayAll()
        self.libvirtInventoryMonitor.collectInventory(self.connection._wrapped_conn, '1')
        self.mock.stubs.UnsetAll()

    def test_collectInventory_conn_none(self):
        self.libvirtInventoryMonitor.collectInventory(None, '1')
        self.mock.stubs.UnsetAll()

    def test_collectInventory_conn_exception(self):
        self.libvirtInventoryMonitor.collectInventory(self.connection, '1')
        self.mock.stubs.UnsetAll()


class test_XMLUtils(unittest.TestCase):

    def setUp(self):
        self.utils = XMLUtils()
        self.ipProfile = IpProfile()
        self.ip_profile_list = []
        self.ipProfile.set_ipAddress('10.10.0.0')
        self.ipProfile.set_hostname('LOCALHOST')
        self.ipProfile.set_ipType("IPV4")
        self.ip_profile_list.append(self.ipProfile)

    def test_is_profile_in_list(self):
        result = self.utils.is_profile_in_list(self.ipProfile, self.ip_profile_list)
        self.assertTrue(result)

    def test_getNodeXML(self):
        xml = '<network><name> NAME </name></network>'
        result = self.utils.getNodeXML(xml, "address")
        self.assertTrue(len(result) == 0)
