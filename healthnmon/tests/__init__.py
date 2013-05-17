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


from healthnmon.db import migration as healthnmon_migration
import FakeLibvirt
from nova.db import migration as nova_migration
from oslo.config import cfg
import __builtin__
import healthnmon
import os
import shutil
import sys

setattr(__builtin__, '_', lambda x: x)

sys.modules['libvirt'] = FakeLibvirt
test_opts = [
    cfg.StrOpt('sqlite_clean_db',
               default='clean.sqlite',
               help='File name of clean sqlite db'),
]
CONF = cfg.CONF
CONF.register_opts(test_opts)
CONF.import_opt('sqlite_db', 'nova.openstack.common.db.sqlalchemy.session')
CONF.import_opt('sqlite_synchronous',
                'nova.openstack.common.db.sqlalchemy.session')
CONF.set_default('sqlite_db', 'tests.sqlite')
CONF.set_default('sqlite_synchronous', False)


def setup():
    ''' for nova test.py create a dummy clean.sqlite '''
    healthnmon_path = os.path.abspath(
        os.path.join(healthnmon.get_healthnmon_location(), '../'))
    cleandb = os.path.join(healthnmon_path, CONF.sqlite_clean_db)
    if os.path.exists(cleandb):
        pass
    else:
        open(cleandb, 'w').close()

    ''' for healthnmon create db '''
    healthnmon_path = os.path.abspath(
        os.path.join(healthnmon.get_healthnmon_location(), '../'))
    sql_connection_url = "sqlite:///" + str(healthnmon_path) + "/$sqlite_db"
    CONF.set_default("sql_connection", sql_connection_url)
    testdb = os.path.join(healthnmon_path, CONF.sqlite_db)
    if os.path.exists(testdb):
        return
    nova_migration.db_sync()
    healthnmon_migration.db_sync()
    cleandb = os.path.join(healthnmon_path, CONF.sqlite_clean_db)
    shutil.copyfile(testdb, cleandb)

""" Uncomment the line below for running tests through eclipse """
# setup()
