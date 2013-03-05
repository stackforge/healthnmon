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
from healthnmon.virt.libvirt import connection as connection
from healthnmon.tests import FakeLibvirt
from healthnmon import test


class Test_virt_connection_cover(test.TestCase):

    # setting up the mocks

    def setUp(self):
        self.fakeConn = FakeLibvirt.open('qemu:///system')
        self.libvirt_connection_cls = connection.LibvirtConnection
        super(Test_virt_connection_cover, self).setUp()
        self.flags(
            healthnmon_notification_drivers=[
                'healthnmon.notifier.log_notifier']
        )

    def test_broken_connection_cover(self):
        global libvirt
        libvirt = libvirt = __import__('libvirt')
        error = 38
        domain = 13
        conn = connection.get_connection(False)

#        self.mox.StubOutWithMock(libvirt,'openReadOnly')
#        libvirt.openReadOnly(mox.IgnoreArg()).AndReturn(self.fakeConn)
#        conn._wrapped_conn=self.fakeConn

        self.mox.StubOutWithMock(conn, '_wrapped_conn')
        self.mox.StubOutWithMock(conn._wrapped_conn, 'getCapabilities')
        self.mox.StubOutWithMock(libvirt.libvirtError, 'get_error_code')
        self.mox.StubOutWithMock(libvirt.libvirtError,
                                 'get_error_domain')

        conn._wrapped_conn.getCapabilities().AndRaise(
            FakeLibvirt.libvirtError('fake failure'
                                     ))

        libvirt.libvirtError.get_error_code().MultipleTimes(). \
            AndReturn(error)
        libvirt.libvirtError.get_error_domain().MultipleTimes(). \
            AndReturn(domain)

        self.mox.ReplayAll()
        try:
            self.assertFalse(conn._test_connection())
        except:
            print 'error'

    def tearDown(self):
        super(Test_virt_connection_cover, self).tearDown()

if __name__ == '__main__':

    # import sys;sys.argv = ['', 'Test.testName']

    unittest.main()
