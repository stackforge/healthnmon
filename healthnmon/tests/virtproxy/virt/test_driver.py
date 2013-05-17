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

from healthnmon.virtproxy.virt.driver import ComputeInventoryDriver
import unittest


class test_InventoryDriver(unittest.TestCase):

    def setUp(self):
        self.ID = ComputeInventoryDriver()

    def test_initrm_context(self):
        self.assertRaises(NotImplementedError, self.ID.init_rmcontext,
                          '10.10.155.165')

    def test_get_host_ip_addr(self):
        self.assertRaises(NotImplementedError, self.ID.get_host_ip_addr)

    def test_update_inventory(self):
        self.assertRaises(
            NotImplementedError, self.ID.update_inventory, 'compute_id')

    def test_update_perfdata(self):
        self.assertRaises(NotImplementedError, self.ID.update_perfdata,
                          'uuid', 'perfmontype')

    def test_get_resource_utilization(self):
        self.assertRaises(NotImplementedError,
                          self.ID.get_resource_utilization, 'uuid',
                          'perfmontype', 5)
