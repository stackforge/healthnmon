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

from healthnmon.api.healthnmon import Healthnmon
from nova.api.openstack.compute import contrib
import unittest
import mox


class FakeExtensionManager:

    def register(self, descriptor):
        pass


class HealthnmonTest(unittest.TestCase):

    def setUp(self):
        """ Setup initial mocks and logging configuration """

        super(HealthnmonTest, self).setUp()
        self.mock = mox.Mox()

    def tearDown(self):
        self.mock.stubs.UnsetAll()

    def test_get_resources(self):
        self.mock.StubOutWithMock(contrib, 'standard_extensions')
        contrib.standard_extensions(mox.IgnoreArg()).AndReturn(None)
        self.assertNotEqual(Healthnmon(FakeExtensionManager()).get_resources(),
                            None)
