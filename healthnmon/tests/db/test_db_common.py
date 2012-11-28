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


"""
    Test cases for common code in db.api modules
"""


from healthnmon.tests.db import test
from healthnmon.db import api as healthnmon_db_api
from healthnmon.db.sqlalchemy import api as healthnmon_alchemy_api
from healthnmon.resourcemodel.healthnmonResourceModel import VmHost, OsProfile
import mox
from nova.context import get_admin_context
from nova.db.sqlalchemy import session as nova_session
import time
from healthnmon.constants import DbConstants


class CommonDbApiTestCase(test.TestCase):

    def setUp(self):
        super(CommonDbApiTestCase, self).setUp()
        self.mock = mox.Mox()
        self.admin_context = get_admin_context()
        self.db_session = nova_session.get_session()

    def tearDown(self):
        super(CommonDbApiTestCase, self).tearDown()
        self.mock.stubs.UnsetAll()

    def test_filtered_ordered_query_changessince_invalid_value(self):
        # Create VmHost
        vmhost = VmHost()
        vmhost.id = 'VH1'
        healthnmon_db_api.vm_host_save(self.admin_context, vmhost)
        # Query with invalid changes-since
        filters = {'changes-since': 'invalid-value'}
        vmhosts = healthnmon_db_api.vm_host_get_all_by_filters(
            self.admin_context, filters,
            None, None)
        self.assert_(vmhosts is not None)
        self.assert_(len(vmhosts) == 1)
        self.assert_(vmhosts[0] is not None)
        self.assert_(vmhosts[0].id == vmhost.id)

    def test_filtered_ordered_query_changessince_no_field(self):
        # Create OsProfile which do not have lastModifiedEpoch field
        os_profile = OsProfile()
        os_profile.set_resourceId('resourceId')
        os_profile.set_osName('Linux')
        self.db_session.merge(os_profile)
        self.db_session.flush()
        self.db_session.expunge_all()
        # Query with changes-since
        now = long(time.time() * 1000L)
        filters = {'changes-since': now}
        query = healthnmon_alchemy_api._create_filtered_ordered_query(
            self.db_session, OsProfile, filters=filters)
        os_profiles = query.all()
        self.assert_(os_profiles is not None)
        self.assert_(len(os_profiles) == 1)
        self.assert_(os_profiles[0] is not None)
        self.assert_(os_profiles[0].osName == os_profile.osName)

    def test_filtered_ordered_query_deleted_no_field(self):
        # Create OsProfile which do not have deleted field
        os_profile = OsProfile()
        os_profile.set_resourceId('resourceId')
        os_profile.set_osName('Linux')
        self.db_session.merge(os_profile)
        self.db_session.flush()
        self.db_session.expunge_all()
        # Query with deleted
        filters = {'deleted': False}
        query = healthnmon_alchemy_api._create_filtered_ordered_query(
            self.db_session, OsProfile, filters=filters)
        os_profiles = query.all()
        self.assert_(os_profiles is not None)
        self.assert_(len(os_profiles) == 1)
        self.assert_(os_profiles[0] is not None)
        self.assert_(os_profiles[0].osName == os_profile.osName)

    def test_filtered_ordered_query_filter_no_field(self):
        # Create OsProfile
        os_profile = OsProfile()
        os_profile.set_resourceId('resourceId')
        os_profile.set_osName('Linux')
        self.db_session.merge(os_profile)
        self.db_session.flush()
        self.db_session.expunge_all()
        # Query with invalidFilterField
        filters = {'invalidFilterField': 'SomeValue'}
        query = healthnmon_alchemy_api._create_filtered_ordered_query(
            self.db_session, OsProfile, filters=filters)
        os_profiles = query.all()
        self.assert_(os_profiles is not None)
        self.assert_(len(os_profiles) == 1)
        self.assert_(os_profiles[0] is not None)
        self.assert_(os_profiles[0].osName == os_profile.osName)

    def test_filtered_ordered_query_sort_no_field(self):
        # Create VmHost
        vmhost = VmHost()
        vmhost.id = 'VH1'
        healthnmon_db_api.vm_host_save(self.admin_context, vmhost)
        # Query with invalid sort key
        vmhosts = healthnmon_db_api.vm_host_get_all_by_filters(
            self.admin_context, None,
            'invalidSortField', DbConstants.ORDER_ASC)
        self.assert_(vmhosts is not None)
        self.assert_(len(vmhosts) == 1)
        self.assert_(vmhosts[0] is not None)
        self.assert_(vmhosts[0].id == vmhost.id)
