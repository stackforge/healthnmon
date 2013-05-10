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

import unittest
from oslo.config import cfg
import os
from healthnmon.db.sqlalchemy import manage_healthnmon_db
from sqlalchemy.engine import create_engine

CONF = cfg.CONF
CONF.set_default('sqlite_db', 'tests.sqlite')
CONF.set_default('sqlite_synchronous', False)


class ManageDbTestCase(unittest.TestCase):

    def test_upgrade_downgrade(self):
        testdb = os.path.join(CONF.state_path, CONF.sqlite_db)

        # Recreate the DB

        if os.path.exists(testdb):
            os.remove(testdb)
        open(testdb, 'w').close()
        engine = create_engine(CONF.sql_connection)

        # manage_healthnmon_db.main(CONF.sql_connection)

        manage_healthnmon_db.upgrade(engine)
        tableExists = manage_healthnmon_db.VmHost.exists(engine)
        self.assertTrue(tableExists, 'Db upgrade failed')

        # manage_healthnmon_db.main(CONF.sql_connection, "downgrade")

        manage_healthnmon_db.downgrade(engine)
        tableExistsAfterDowngrade = \
            manage_healthnmon_db.VmHost.exists(engine)
        self.assertFalse(tableExistsAfterDowngrade,
                         'Db downgrade failed')

    def test_upgrade_downgrade_exception(self):
        testdb = os.path.join(CONF.state_path, CONF.sqlite_db)

        # Recreate the DB

        if os.path.exists(testdb):
            os.remove(testdb)
        open(testdb, 'w').close()

        self.assertRaises(Exception, manage_healthnmon_db.upgrade,
                          'exception')

        self.assertRaises(Exception, manage_healthnmon_db.downgrade,
                          'exception')
