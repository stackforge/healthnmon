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
Created on Feb 20, 2012

@author: Rahul Krishna Upadhyaya
'''

import unittest
import mox
from healthnmon.virt.libvirt import connection as connection
from healthnmon import rmcontext as rmcontext
from healthnmon.constants import Constants
from healthnmon.db import api
from healthnmon.inventory_manager import ComputeInventory
from healthnmon.inventory_cache_manager import InventoryCacheManager
from healthnmon.rmcontext import ComputeRMContext
from healthnmon.perfmon import libvirt_perfdata
from nova import test
from healthnmon.tests import FakeLibvirt as libvirt


class Test_virt_connection(test.TestCase):

    # setting up the mocks

    def setUp(self):
        self.fakeConn = libvirt.open('qemu:///system')
        self.libvirt_connection_cls = connection.LibvirtConnection
        super(Test_virt_connection, self).setUp()
        self.flags(
            healthnmon_notification_drivers=[
                'healthnmon.notifier.log_notifier']
        )

    def test_init_rmcontext(self):
        compute_rmcontext = rmcontext.ComputeRMContext(
            rmType='QEMU',
            rmIpAddress='10.10.155.165', rmUserName='openstack',
            rmPassword='password')
        conn = connection.get_connection(True)
        conn.init_rmcontext(compute_rmcontext)
        self.assertTrue(conn.compute_rmcontext is not None)
        self.assertEquals(conn.compute_rmcontext.rmIpAddress, "10.10.155.165")
        self.assertEquals(conn.compute_rmcontext.rmUserName, "openstack")
        self.assertEquals(conn.compute_rmcontext.rmPassword, "password")

    def test__get_connection_with_conn(self):

        conn = connection.get_connection(True)
        compute_rmcontext = ComputeRMContext(
            rmType='QEMU',
            rmIpAddress='10.10.155.165', rmUserName='openstack',
            rmPassword='password')
        conn.init_rmcontext(compute_rmcontext)
        conn._wrapped_conn = self.fakeConn
        result = conn._get_connection()
        assert result

    def test__get_connection_with_invalid_conn(self):

        conn = connection.get_connection(True)
        compute_rmcontext = ComputeRMContext(
            rmType='QEMU',
            rmIpAddress='10.10.155.165', rmUserName='openstack',
            rmPassword='password')
        conn.init_rmcontext(compute_rmcontext)
        conn._wrapped_conn = 'Invalid'
        self.assertRaises(Exception, conn._get_connection)

    def test_update_inventory(self):
        self.mox.StubOutWithMock(libvirt, 'openReadOnly')
        libvirt.openReadOnly(mox.IgnoreArg()).AndReturn(self.fakeConn)
        self.mox.StubOutWithMock(api, 'vm_save')
        self.mox.StubOutWithMock(api, 'vm_host_save')
        self.mox.StubOutWithMock(api, 'storage_volume_save')

        api.storage_volume_save(
            mox.IgnoreArg(),
            mox.IgnoreArg()).MultipleTimes().AndReturn(None)

        api.vm_host_save(mox.IgnoreArg(),
                         mox.IgnoreArg()).MultipleTimes().AndReturn(None)

        api.vm_save(mox.IgnoreArg(),
                    mox.IgnoreArg()).MultipleTimes().AndReturn(None)
        self.mox.ReplayAll()
        conn = connection.get_connection(True)
        compute_rmcontext = ComputeRMContext(
            rmType='QEMU',
            rmIpAddress='10.10.155.165', rmUserName='openstack',
            rmPassword='password')

        InventoryCacheManager.get_all_compute_inventory()['1'] = \
            ComputeInventory(compute_rmcontext)

        conn.init_rmcontext(compute_rmcontext)
        conn._wrapped_conn = self.fakeConn

        conn.update_inventory('1')

    def test_get_inventory_monitor(self):
        conn1 = connection.get_connection(True)
        libvirt_inv = conn1.get_inventory_monitor()
        assert libvirt_inv

    def test_get_inventory_monitor_None(self):
        conn1 = connection.get_connection(True)
        self.assertTrue(conn1.get_inventory_monitor() is not None)
        self.assertTrue(conn1.get_perf_monitor() is not None)
        conn1.libvirt_invmonitor = None
        conn1.get_inventory_monitor()
        self.assertTrue(conn1.get_inventory_monitor() is None)

    def test_test_connection(self):
        conn1 = connection.get_connection(True)
        conn1._wrapped_conn = self.fakeConn
        flag = conn1._test_connection()
        assert flag, True

    def test_get_new_connection(self):
        libvirtcon = connection.get_connection(True)
        libvirtcon.get_new_connection("wrong:///uri", True)

    def test_uri_uml(self):
        self.flags(libvirt_type='uml')
        conn1 = connection.get_connection(True)
        self.assertEquals(conn1.uri, "uml:///system")

    def test_uri_xen(self):
        self.flags(libvirt_type='xen')
        conn1 = connection.get_connection(True)
        self.assertEquals(conn1.uri, "xen:///")

    def test_uri_lxc(self):
        self.flags(libvirt_type='lxc')
        conn1 = connection.get_connection(True)
        self.assertEquals(conn1.uri, "lxc:///")

    def test_update_perfdata(self):

        self.mox.StubOutWithMock(libvirt_perfdata.LibvirtPerfMonitor,
                                 'refresh_perfdata')
        libvirt_perfdata.LibvirtPerfMonitor.refresh_perfdata(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            mox.IgnoreArg()).AndReturn('')
        self.mox.ReplayAll()

        conn = connection.get_connection(True)
        compute_rmcontext = ComputeRMContext(
            rmType='QEMU',
            rmIpAddress='10.10.155.165', rmUserName='openstack',
            rmPassword='password')
        conn.init_rmcontext(compute_rmcontext)
        conn._wrapped_conn = self.fakeConn
        conn.update_perfdata('uuid', 'perfmon_type')
        self.assertTrue(conn.libvirt_perfmon.perfDataCache is not None)

    def test_get_resource_utilization(self):

        self.mox.StubOutWithMock(libvirt_perfdata.LibvirtPerfMonitor,
                                 'get_resource_utilization')
        libvirt_perfdata.LibvirtPerfMonitor.get_resource_utilization(
            mox.IgnoreArg(),
            mox.IgnoreArg(), mox.IgnoreArg()).AndReturn('')
        self.mox.ReplayAll()
        conn1 = connection.get_connection(True)
        self.assertTrue(conn1.get_resource_utilization('uuid',
                                                       'perfmon_type',
                                                       'window_minutes') is '')
        self.assertTrue(conn1.libvirt_perfmon.perfDataCache is not None)

    def test_get_resource_utilization_None(self):
        libvirt_conn = connection.LibvirtConnection(True)
        libvirt_conn.libvirt_perfmon = None
        conn1 = connection.get_connection(True)
        self.assertTrue(
            libvirt_conn.get_resource_utilization('uuid', 'perfmon_type',
                                                  'window_minutes') is None)
        self.assertTrue(conn1.libvirt_perfmon.perfDataCache.get(
            'old_stats') is None)
        self.assertTrue(conn1.libvirt_perfmon.perfDataCache.get(
            'new_stats') is None)

    def test_get_perf_monitor(self):
        conn1 = connection.get_connection(True)
        libvirt_perform = conn1.get_perf_monitor()
        assert libvirt_perform

    def test_get_perf_monitor_None(self):
        conn1 = connection.get_connection(True)
        conn1.libvirt_perfmon = None
        self.assertTrue(conn1.get_perf_monitor() is None)

    def test_broken_connection_remote(self):

        libvirtError = libvirt.libvirtError('fake failure')

#        libError = self.mox.CreateMockAnything()
#        self.stubs.Set(libvirt.libvirtError, '__init__', libError)
#        libError('fake failure').AndReturn(libvirtError)

        capability = self.mox.CreateMockAnything()
        self.stubs.Set(libvirt.virConnect, 'getCapabilities',
                       capability)
        capability().AndRaise(libvirtError)

#        self.mox.StubOutWithMock(libvirt.libvirtError, "get_error_domain")
#
#        libvirt.libvirtError.get_error_code().AndReturn(error)
#        libvirt.libvirtError.get_error_domain().AndReturn(domain)

        self.mox.ReplayAll()
        conn = connection.get_connection(False)
        conn._wrapped_conn = self.fakeConn

        try:
            self.assertFalse(conn._test_connection())
        except:
            print 'over'

    def test_get_connection_with_conn_static(self):

        self.mox.StubOutWithMock(libvirt, 'openReadOnly')
        libvirt.openReadOnly(mox.IgnoreArg()).AndReturn(self.fakeConn)
        self.mox.ReplayAll()
        con = self.libvirt_connection_cls._connect('uri', True)
        self.assertEquals("ubuntu164.vmm.hp.com", con.getHostname())
        self.assertTrue("ReleaseBDevEnv" in con.listDefinedDomains())
        self.assertTrue("1" in str(con.listDomainsID()))

    def test_get_connection_with_conn_static_exception(self):

        self.mox.StubOutWithMock(libvirt, 'openReadOnly')
        libvirt.openReadOnly(mox.IgnoreArg()).AndRaise(libvirt.libvirtError)
        self.mox.ReplayAll()
        try:
            self.libvirt_connection_cls._connect('uri', True)
        except Exception as e:
            self.assertTrue(isinstance(e, libvirt.libvirtError))

    def test_get_connection_with_conn_static_False(self):

        self.mox.StubOutWithMock(libvirt, 'openAuth')

        libvirt.openAuth(mox.IgnoreArg(), mox.IgnoreArg(),
                         mox.IgnoreArg()).AndReturn(self.fakeConn)
        self.mox.ReplayAll()
        con = self.libvirt_connection_cls._connect('uri', False)
        self.assertEquals("ubuntu164.vmm.hp.com", con.getHostname())
        self.assertTrue("ReleaseBDevEnv" in con.listDefinedDomains())
        self.assertTrue("1" in str(con.listDomainsID()))

    def test_rmcontext_exception(self):

        try:
            compute_rmcontext = ComputeRMContext(
                rmType='QEMU',
                rmIpAddress='10.10.155.165', rmUserName='openstack',
                rmPassword='password')

            compute_rmcontext.__getattribute__('test'
                                               ).AndRaise(AttributeError)
        except Exception, e:
            self.assertEquals(type(e), AttributeError)

if __name__ == '__main__':

    # import sys;sys.argv = ['', 'Test.testName']

    unittest.main()
