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

from healthnmon.db import api
from healthnmon.resourcemodel.healthnmonResourceModel import PortGroup, Cost
from healthnmon import test
from nova.openstack.common.db.sqlalchemy import session as db_session
from nova.context import get_admin_context
from healthnmon import utils
from healthnmon.tests import utils as test_utils
from decimal import Decimal


class PortGroupDbApiTestCase(test.TestCase):

    def setUp(self):
        super(PortGroupDbApiTestCase, self).setUp()
        # self.mock = mox.Mox()

    def tearDown(self):
        super(PortGroupDbApiTestCase, self).tearDown()
        # self.mock.stubs.UnsetAll()

    def test_port_group_save(self):
        portgroup = PortGroup()
        portgroup.id = 'PG1'
        portgroup.name = 'test'
        portgroup.note = 'note'
        api.port_group_save(get_admin_context(), portgroup)

        portgroup = PortGroup()
        portgroup.id = 'PG1'
        portgroup.name = 'test'
        portgroup.note = 'note'
        cost = Cost()
        cost.value = Decimal('123.00')
        cost.units = 'INR'
        portgroup.cost = cost
        portgroup.resourceManagerId = 'rm1'
        portgroup.type = 'port'
        portgroup.virtualSwitchId = 'VS1'
        portgroup.vmHostId = 'VM1'
        api.port_group_save(get_admin_context(), portgroup)
        pgs = api.port_group_get_by_ids(get_admin_context(),
                                        [portgroup.id])

        indexOfThePG = -1
        for pg in pgs:
            if pg.id == portgroup.id:
                indexOfThePG = pgs.index(pg)
                break

        self.assertTrue(
            portgroup.id == pgs[indexOfThePG].id, 'Portgroup id is invalid')
        self.assertTrue(portgroup.name == pgs[indexOfThePG].name,
                        ' PortGroup name is invalid')
        self.assertTrue(portgroup.note == pgs[indexOfThePG].note,
                        'PortGroup Note is invalid')
        self.assertTrue(portgroup.cost.value == pgs[indexOfThePG]
                        .cost.value, 'PortGroup Value is invalid')
        self.assertTrue(portgroup.cost.units == pgs[indexOfThePG]
                        .cost.units, 'PortGroup Units is invalid')
        self.assertTrue(
            portgroup.resourceManagerId == pgs[indexOfThePG].resourceManagerId,
            'PortGroup resourceManagerId is invalid')
        self.assertTrue(portgroup.get_type(
        ) == pgs[indexOfThePG].get_type(), 'PortGroup type is invalid')
        self.assertTrue(
            portgroup.virtualSwitchId == pgs[indexOfThePG].virtualSwitchId,
            'PortGroup virtualSwitchId is invalid')
        self.assertTrue(portgroup.vmHostId == pgs[indexOfThePG]
                        .vmHostId, 'PortGroup vmHostId is invalid')

        self.assertTrue(len(pgs) == 1,
                        'port groups all returned valid number of list')

    def test_port_group_save_none(self):
        self.assertTrue(api.port_group_save(get_admin_context(
        ), None) is None, 'Port group save none should save nothing')

    def test_port_group_get_all(self):

        portgroup = PortGroup()

        portgroup.id = 'PG1'
        portgroup.name = 'test'
        portgroup.note = 'note'
        cost = Cost()
        cost.value = Decimal('123.00')
        cost.units = 'INR'
        portgroup.cost = cost
        portgroup.resourceManagerId = 'rm1'
        portgroup.type = 'port'
        portgroup.virtualSwitchId = 'VS1'
        portgroup.vmHostId = 'VM1'
        api.port_group_save(get_admin_context(), portgroup)
        pgs = api.port_group_get_all(get_admin_context())
        indexOfThePG = -1
        for pg in pgs:
            if pg.id == portgroup.id:
                indexOfThePG = pgs.index(pg)
                break

        self.assertTrue(
            portgroup.id == pgs[indexOfThePG].id, 'Portgroup id is invalid')
        self.assertTrue(portgroup.name == pgs[indexOfThePG].name,
                        ' PortGroup name is invalid')
        self.assertTrue(portgroup.note == pgs[indexOfThePG].note,
                        'PortGroup Note is invalid')
        self.assertTrue(portgroup.cost.value == pgs[indexOfThePG]
                        .cost.value, 'PortGroup Value is invalid')
        self.assertTrue(portgroup.cost.units == pgs[indexOfThePG]
                        .cost.units, 'PortGroup Units is invalid')
        self.assertTrue(
            portgroup.resourceManagerId == pgs[indexOfThePG].resourceManagerId,
            'PortGroup resourceManagerId is invalid')
        self.assertTrue(portgroup.get_type(
        ) == pgs[indexOfThePG].get_type(), 'PortGroup type is invalid')
        self.assertTrue(
            portgroup.virtualSwitchId == pgs[indexOfThePG].virtualSwitchId,
            'PortGroup virtualSwitchId is invalid')
        self.assertTrue(portgroup.vmHostId == pgs[indexOfThePG]
                        .vmHostId, 'PortGroup vmHostId is invalid')

        self.assertFalse(pgs is None,
                         'port groups all returned a none list')
        self.assertTrue(len(pgs) == 1,
                        'port groups all returned valid number of list')

    def test_port_group_get_by_id(self):
        portgroup = PortGroup()
        portgroup.id = 'PG1'
        portgroup.name = 'test'
        portgroup.note = 'note'
        cost = Cost()
        cost.value = Decimal('123.00')
        cost.units = 'INR'
        portgroup.cost = cost
        portgroup.resourceManagerId = 'rm1'
        portgroup.type = 'port'
        portgroup.virtualSwitchId = 'VS1'
        portgroup.vmHostId = 'VM1'
        api.port_group_save(get_admin_context(), portgroup)

        pgs = api.port_group_get_by_ids(get_admin_context(),
                                        [portgroup.id])

        indexOfThePG = -1
        for pg in pgs:
            if pg.id == portgroup.id:
                indexOfThePG = pgs.index(pg)
                break

        self.assertTrue(
            portgroup.id == pgs[indexOfThePG].id, 'Portgroup id is invalid')
        self.assertTrue(portgroup.name == pgs[indexOfThePG].name,
                        ' PortGroup name is invalid')
        self.assertTrue(portgroup.note == pgs[indexOfThePG].note,
                        'PortGroup Note is invalid')
        self.assertTrue(portgroup.cost.value == pgs[indexOfThePG]
                        .cost.value, 'PortGroup Value is invalid')
        self.assertTrue(portgroup.cost.units == pgs[indexOfThePG]
                        .cost.units, 'PortGroup Units is invalid')
        self.assertTrue(
            portgroup.resourceManagerId == pgs[indexOfThePG].resourceManagerId,
            'PortGroup resourceManagerId is invalid')
        self.assertTrue(portgroup.get_type(
        ) == pgs[indexOfThePG].get_type(), 'PortGroup type is invalid')
        self.assertTrue(
            portgroup.virtualSwitchId == pgs[indexOfThePG].virtualSwitchId,
            'PortGroup virtualSwitchId is invalid')
        self.assertTrue(portgroup.vmHostId == pgs[indexOfThePG]
                        .vmHostId, 'PortGroup vmHostId is invalid')

        self.assertTrue(len(pgs) == 1,
                        'port groups all returned valid number of list')

    def test_port_group_get_by_id_empty_list(self):
        pgs = api.port_group_get_by_ids(get_admin_context(), None)
        self.assertTrue(
            pgs is None, 'The returned Portgroups list should be empty')

    def test_port_group_delete_empty_list(self):
        self.assertTrue(api.port_group_delete_by_ids(get_admin_context(
        ), None) is None, 'This method should return None')

    def test_port_group_delete(self):
        portgroup = PortGroup()
        portgroup.id = 'PG1'
        portgroup.name = 'test'
        portgroup.note = 'note'
        from decimal import Decimal
        portgroup.value = Decimal('123.00')
        portgroup.units = 'uni'
        portgroup.resourceManagerId = 'rm1'
        portgroup.type = 'port'
        portgroup.virtualSwitchId = 'VS1'
        portgroup.vmHostId = 'VM1'
        api.port_group_save(get_admin_context(), portgroup)

        pgs = api.port_group_get_by_ids(get_admin_context(),
                                        [portgroup.id])
        self.assertFalse(len(pgs) == 0, 'Portgroup could not be saved')

        api.port_group_delete_by_ids(get_admin_context(),
                                     [portgroup.id])
        portgroups = api.port_group_get_by_ids(get_admin_context(),
                                               [portgroup.id])

        self.assertTrue(portgroups is None or len(portgroups) == 0,
                        'port group not deleted')

    def test_port_group_save_throw_exception(self):
        self.assertRaises(Exception, api.port_group_save,
                          get_admin_context(), PortGroup())

    def test_port_group_get_ids_throw_exception(self):
        self.mox.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mox.ReplayAll()
        self.assertRaises(Exception, api.port_group_get_by_ids,
                          get_admin_context(), ['portgroup-01'])

    def test_port_group_get_all_throw_exception(self):
        self.mox.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mox.ReplayAll()
        self.assertRaises(Exception, api.port_group_get_all,
                          get_admin_context())

    def test_port_group_delete_throw_exception(self):
        self.mox.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mox.ReplayAll()
        self.assertRaises(Exception, api.port_group_delete_by_ids,
                          get_admin_context(), ['portgroup-01'])

    def test_timestamp_columns(self):
        """
            Test the time stamp columns createEpoch,
            modifiedEpoch and deletedEpoch
        """
        portGrp = PortGroup()
        portGrp.set_id('portGrp-01')
        # Check for createEpoch
        epoch_before = utils.get_current_epoch_ms()
        api.port_group_save(get_admin_context(), portGrp)
        epoch_after = utils.get_current_epoch_ms()
        portGrp_queried = api.port_group_get_by_ids(
            get_admin_context(), [portGrp.get_id()])[0]
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after, portGrp_queried.get_createEpoch()))
        # Check for lastModifiedEpoch
        portGrp_modified = portGrp_queried
        test_utils.unset_timestamp_fields(portGrp_modified)
        portGrp_modified.set_name('changed_name')
        epoch_before = utils.get_current_epoch_ms()
        api.port_group_save(get_admin_context(), portGrp_modified)
        epoch_after = utils.get_current_epoch_ms()
        portGrp_queried = api.port_group_get_by_ids(
            get_admin_context(), [portGrp.get_id()])[0]
        self.assert_(portGrp_modified.get_createEpoch(
        ) == portGrp_queried.get_createEpoch())
        self.assert_(test_utils.is_timestamp_between(
            epoch_before,
            epoch_after,
            portGrp_queried.get_lastModifiedEpoch()))
