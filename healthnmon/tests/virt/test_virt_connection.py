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

'''Created on Feb 20, 2012

@author: Rahul Krishna Upadhyaya
'''

import unittest
import mox
from healthnmon.virt import connection
from healthnmon.virt.libvirt import connection as libvirt_conn


class Test_connection(unittest.TestCase):

    # setting up the mocks

    def setUp(self):
        self.mock = mox.Mox()

    # Mock a module-level function get_connection in a connection module

    def test_get_connection(self):
        conn = libvirt_conn.LibvirtConnection(True)
        conn1 = None

        self.mock.StubOutWithMock(libvirt_conn, 'get_connection')

        libvirt_conn.get_connection(True).AndReturn(conn)
        libvirt_conn.get_connection(False).AndReturn(conn1)

        # running all the mocks

        self.mock.ReplayAll()

        # performing assert operations

        self.assertTrue(connection.get_connection('QEMU', True))
        self.assertTrue(connection.get_connection('fake', True))
        self.assertRaises(Exception, connection.get_connection, 'xyz',
                          True)

        # Unsetting all the mocks

        self.mock.UnsetStubs()

    def test_get_connection_exception(self):

        self.mock.StubOutWithMock(libvirt_conn, 'get_connection')
        libvirt_conn.get_connection(True).AndReturn(None)

        # running all the mocks

        self.mock.ReplayAll()

        try:

            connection.get_connection('QEMU', True)
        except SystemExit, e:

            self.assertEquals(type(e), type(SystemExit()))
            self.assertEquals(e.code, 1)
        except Exception, e:
            self.fail('unexpected exception: %s' % e)
        else:
            self.fail('SystemExit exception expected')

        # Unsetting all the mocks

        self.mock.UnsetStubs()


if __name__ == '__main__':

    # import sys;sys.argv = ['', 'Test.testName']

    unittest.main()
