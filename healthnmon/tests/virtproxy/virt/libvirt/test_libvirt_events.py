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

'''
Created on Sep 25, 2012

@author: root
'''
from healthnmon.tests import FakeLibvirt as libvirt
from healthnmon.virtproxy.virt.libvirt import libvirt_event_monitor
from healthnmon.virtproxy.virt.libvirt.connection import LibvirtConnection
import mox
from healthnmon.rmcontext import ComputeRMContext
import unittest
from healthnmon.virtproxy.virt.libvirt import libvirt_inventorymonitor
from healthnmon.virtproxy.inventory_cache_manager import InventoryCacheManager
from healthnmon.virtproxy.inventory_manager import ComputeInventory
import eventlet


class test_LibvirtEvents(unittest.TestCase):

    def setUp(self):
        self.mock = mox.Mox()

    def tearDown(self):
        self.mock.stubs.UnsetAll()

    def test_register_libvirt_events(self):
        libvirtEvents = libvirt_event_monitor.LibvirtEvents()
        libvirtEvents.compute_id = '1'
        connection = LibvirtConnection(False)
        connection.compute_rmcontext = \
            ComputeRMContext(rmType='fake', rmIpAddress='10.10.155.165',
                             rmUserName='openstack',
                             rmPassword='password')
        InventoryCacheManager.get_all_compute_inventory()['1'] = \
            ComputeInventory(connection.compute_rmcontext)
        libvirtEvents.register_libvirt_events()
        self.mock.VerifyAll()

    def test_register_libvirt_events_conn_none(self):
        libvirtEvents = libvirt_event_monitor.LibvirtEvents()
        libvirtEvents.compute_id = '1'
        connection = LibvirtConnection(False)
        connection.compute_rmcontext = \
            ComputeRMContext(rmType='fake', rmIpAddress='10.10.155.165',
                             rmUserName='openstack',
                             rmPassword='password')
        InventoryCacheManager.get_all_compute_inventory()['2'] = \
            ComputeInventory(connection.compute_rmcontext)
        from healthnmon.virtproxy.virt.fake import FakeConnection
        self.mock.StubOutWithMock(FakeConnection, 'get_new_connection')
        fc = FakeConnection()
        fc.get_new_connection(mox.IgnoreArg(), mox.IgnoreArg()).AndReturn(None)
        self.mock.ReplayAll()
        libvirtEvents.register_libvirt_events()
        self.mock.VerifyAll()

    def test_register_libvirt_eventsException(self):
        libvirtEvents = libvirt_event_monitor.LibvirtEvents()
        libvirtEvents.register_libvirt_events()

    def test__register_libvirt_domain_events(self):
        libvirt_event_monitor.libvirt = libvirt
        libvirtEvents = libvirt_event_monitor.LibvirtEvents()
        libvirtEvents.libvirt_con = libvirt.openReadOnly('fake:///system')
        libvirtEvents._register_libvirt_domain_events()

    def test_deregister_libvirt_events(self):
        libvirtEvents = libvirt_event_monitor.LibvirtEvents()
        libvirtEvents.registered = True
        libvirtEvents.call_back_ids['domain_events'] = [1]
        libvirtEvents.libvirt_con = libvirt.open("fake:///system")
        libvirtEvents.deregister_libvirt_events()
        self.mock.VerifyAll()

    def test_deregister_libvirt_events_Exception(self):
        libvirtEvents = libvirt_event_monitor.LibvirtEvents()
        libvirtEvents.registered = True
        libvirtEvents.call_back_ids['domain_events'] = [1, 2, 3]
        libvirtEvents.deregister_libvirt_events()

    def test_deregister_libvirt_domain_events(self):
        libvirtEvents = libvirt_event_monitor.LibvirtEvents()
        libvirtEvents.call_back_ids['domain_events'] = [1]
        libvirtEvents.libvirt_con = libvirt.open("fake:///system")
        libvirtEvents._deregister_libvirt_domain_events()

    def test__process_updates_for_updated_domain(self):
        self.mock.StubOutClassWithMocks(libvirt_inventorymonitor, 'LibvirtVM')
        mocked_libvirtVM = libvirt_inventorymonitor.LibvirtVM(None, None)
        mocked_libvirtVM.process_updates_for_updated_VM(
            mox.IgnoreArg()).AndReturn(None)
        self.mock.ReplayAll()
        libvirtEvents = libvirt_event_monitor.LibvirtEvents()
        libvirtEvents._process_updates_for_updated_domain(None)
        self.mock.VerifyAll()

    def test_domain_event_callback(self):
        libvirt_event_monitor.pool_for_processing_updated_vm =\
            eventlet.greenpool.GreenPool(200)
        self.mock.StubOutWithMock(
            libvirt_event_monitor.pool_for_processing_updated_vm, 'spawn_n')
        libvirt_event_monitor.pool_for_processing_updated_vm.spawn_n(
            mox.IgnoreArg(), mox.IgnoreArg()).AndReturn(None)
        self.mock.ReplayAll()
        libvirtEvents = libvirt_event_monitor.LibvirtEvents()
        libvirtEvents._domain_event_callback('DummyParam1', 'DummyParam2')
        self.mock.VerifyAll()

    def test__domain_event_callback_exception(self):
        libvirtEvents = libvirt_event_monitor.LibvirtEvents()
        libvirtEvents._domain_event_callback()

    def test_startEventsThread_exception(self):
        domain_event_thread = libvirt_event_monitor.DomainEventThread
        self.mock.StubOutWithMock(domain_event_thread, "start")
        domain_event_thread.start().AndRaise(Exception)
        self.mock.ReplayAll()
        libvirt_event_monitor.start_events_thread()
        self.mock.VerifyAll()
