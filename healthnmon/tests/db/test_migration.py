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

import mox
from healthnmon.db import migration
from healthnmon import test
from migrate.versioning import api as versioning_api
try:
    from migrate.versioning import exceptions as versioning_exceptions
except ImportError:
    from migrate import exceptions as versioning_exceptions


class MigrationTestCase(test.TestCase):

    """Test case for scheduler manager"""

    def setUp(self):
        super(MigrationTestCase, self).setUp()
        # self.mox = mox.Mox()

    def test_dbSync(self):
        self.assertEqual(migration.db_sync(0), None)

    def test_dbVersion(self):
        self.assertNotEqual(migration.db_version(), None)

    def test_dbSync_withValueError(self):
        self.assertRaises(Exception, migration.db_sync, '')

    def test_dbSync_downgrade(self):
        self.assertEqual(migration.db_sync(1), None)

    def test_dbSync_versionNone(self):
        self.assertEqual(migration.db_sync(None), None)

    def test_dbSync_withException(self):
        self.mox.StubOutWithMock(versioning_api, 'db_version')

        versioning_api.db_version(mox.IgnoreArg(),
                                  mox.IgnoreArg()).MultipleTimes(). \
            AndRaise(
                versioning_exceptions.DatabaseNotControlledError)
        self.mox.ReplayAll()
        self.assertRaises(Exception, migration.db_sync, '0')
        self.mox.UnsetStubs()
