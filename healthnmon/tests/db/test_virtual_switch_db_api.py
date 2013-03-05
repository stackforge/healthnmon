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
from healthnmon.resourcemodel.healthnmonResourceModel import VirtualSwitch, \
    Subnet, Cost, PortGroup
from healthnmon import test
from nova.db.sqlalchemy import session as db_session
import mox
from nova.context import get_admin_context
from healthnmon.constants import DbConstants
import time
from healthnmon import utils
from healthnmon.tests import utils as test_utils


class VirtualSwitchDbApiTestCase(test.TestCase):

    def setUp(self):
        super(VirtualSwitchDbApiTestCase, self).setUp()
        # self.mock = mox.Mox()
        self.admin_context = get_admin_context()

    def tearDown(self):
        super(VirtualSwitchDbApiTestCase, self).tearDown()
        # self.mock.stubs.UnsetAll()

    def __create_virtual_switch(self, **kwargs):
        switch = VirtualSwitch()
        if kwargs is not None:
            for field in kwargs:
                setattr(switch, field, kwargs[field])
        api.virtual_switch_save(self.admin_context, switch)
        return switch

    def __create_subnet(self, **kwargs):
        subnet = Subnet()
        if kwargs is not None:
            for field in kwargs:
                setattr(subnet, field, kwargs[field])
        api.subnet_save(self.admin_context, subnet)
        return subnet

    def test_virtual_switch_save_none(self):
        self.assertTrue(api.virtual_switch_save(self.admin_context,
                        None) is None, 'No Virtual Switch should be saved')

    def test_virtual_switch_save(self):
        virtualswitch = VirtualSwitch()
        virtualswitch.id = 'VS1'
        virtualswitch.switchType = 'switch'
        api.virtual_switch_save(self.admin_context, virtualswitch)
        virtualswitches = \
            api.virtual_switch_get_by_ids(self.admin_context,
                                          [virtualswitch.id])
        self.assertFalse(virtualswitches is None,
                         'VirtualSwitch  all returned a list')
        self.assertTrue(
            virtualswitches[0].id == 'VS1', 'Virtual Switch id mismatch')
        self.assertTrue(virtualswitches[0].switchType == 'switch',
                        'Virtual Switch type mismatch')

    def test_virtual_switch_save_update(self):
        virtualswitch = VirtualSwitch()
        virtualswitch.id = 'VS1'
        virtualswitch.switchType = 'switch'
        api.virtual_switch_save(self.admin_context, virtualswitch)
        virtualswitch.switchType = 'switchUpdated'
        api.virtual_switch_save(self.admin_context, virtualswitch)
        virtualswitches = \
            api.virtual_switch_get_by_ids(self.admin_context,
                                          [virtualswitch.id])
        self.assertFalse(virtualswitches is None,
                         'VirtualSwitch  all returned a list')
        self.assertTrue(
            virtualswitches[0].id == 'VS1', 'Virtual Switch id mismatch')
        self.assertTrue(virtualswitches[0].switchType == 'switchUpdated',
                        'Virtual Switch type mismatch')

    def test_virtual_switch_get_by_ids_none(self):
        virtualswitches = \
            api.virtual_switch_get_by_ids(self.admin_context, None)
        self.assertTrue(virtualswitches is None,
                        'VirtualSwitch  all returned a none list')

    def test_virtual_switch_get_by_ids(self):
        virtualswitch = VirtualSwitch()
        virtualswitch.id = 'VS1'
        virtualswitch.switchType = 'switch'
        api.virtual_switch_save(self.admin_context, virtualswitch)
        virtualswitches = \
            api.virtual_switch_get_by_ids(self.admin_context,
                                          [virtualswitch.id])
        self.assertFalse(virtualswitches is None,
                         'VirtualSwitch  all returned a list')
        self.assertTrue(
            virtualswitches[0].id == 'VS1', 'Virtual Switch Id mismatch')
        self.assertTrue(virtualswitches[0].switchType == 'switch',
                        'Virtual Switch Type mismatch')

    def test_virtual_switch_get_all(self):
        virtualswitch = VirtualSwitch()
        virtualswitch.id = 'VS1'
        virtualswitch.switchType = 'switch'
        api.virtual_switch_save(self.admin_context, virtualswitch)
        virtualswitches = api.virtual_switch_get_all(self.admin_context)
        self.assertFalse(virtualswitches is None,
                         'virtual_switch all returned a none list')
        self.assertTrue(len(virtualswitches) == 1,
                        'virtual_switch all returned invalid number of list')
        self.assertTrue(
            virtualswitches[0].id == 'VS1', 'Virtual Switch Id mismatch')
        self.assertTrue(virtualswitches[0].switchType == 'switch',
                        'Virtual Switch Type mismatch')

    def test_virtual_switch_save_with_subnet(self):
        # Save virtual switch with a port group
        vSwitch = VirtualSwitch()
        vSwitch.set_id('vSwitch-11')
        vSwitch.set_name('vSwitch-11')
        vSwitch.set_resourceManagerId('rmId')
        vSwitch.set_switchType('vSwitch')
        cost1 = Cost()
        cost1.set_value(100)
        cost1.set_units('USD')
        vSwitch.set_cost(cost1)
        portGroup = PortGroup()
        portGroup.set_id('pg-01')
        portGroup.set_name('pg-01')
        portGroup.set_resourceManagerId('rmId')
        portGroup.set_type('portgroup_type')
        portGroup.set_cost(cost1)
        vSwitch.add_portGroups(portGroup)
        api.virtual_switch_save(self.admin_context, vSwitch)
        # Update after adding a port group and subnet
        vSwitch = api.virtual_switch_get_by_ids(self.admin_context,
                                                [vSwitch.id])[0]
        portGroup2 = PortGroup()
        portGroup2.set_id('pg-02')
        portGroup2.set_name('pg-02')
        portGroup2.set_resourceManagerId('rmId')
        portGroup2.set_type('portgroup_type')
        vSwitch.add_portGroups(portGroup2)
        subnet = Subnet()
        subnet.set_id('subnet-02')
        subnet.set_name('subnet-02')
        subnet.set_networkAddress('1.1.1.1')
        api.subnet_save(self.admin_context, subnet)
        vSwitch.add_subnetIds(subnet.id)
        vSwitch.add_networkInterfaces('1')
        api.virtual_switch_save(self.admin_context, vSwitch)
        virtualswitches = \
            api.virtual_switch_get_by_ids(self.admin_context,
                                          [vSwitch.id])
        # Assert the values
        self.assertTrue(len(virtualswitches) == 1,
                        'Unexpected number of Virtual Switch returned')
        self.assertTrue(virtualswitches[0].get_id(
        ) == 'vSwitch-11', 'Virtual Switch id mismatch')
        self.assertTrue(virtualswitches[0].get_name(
        ) == 'vSwitch-11', 'Virtual Switch name mismatch')
        self.assertTrue(virtualswitches[0].get_resourceManagerId(
        ) == 'rmId', 'Virtual Switch Resource Manager id mismatch')
        self.assertTrue(virtualswitches[0].get_switchType(
        ) == 'vSwitch', 'Virtual Switch type mismatch')
        cost1 = virtualswitches[0].get_cost()
        self.assertTrue(
            cost1.get_value() == 100, 'VSwitch Cost Value mismatch')
        self.assertTrue(
            cost1.get_units() == 'USD', 'VSwitch Cost units mismatch')
        portGroups = virtualswitches[0].get_portGroups()
        self.assertTrue(
            len(portGroups) == 2, 'All the portgroups have not been saved')
        self.assertTrue(portGroups[0].get_id(
        ) == 'pg-01', 'VSwitch Port Group id mismatch')
        self.assertTrue(portGroups[0].get_name(
        ) == 'pg-01', 'VSwitch Port Group Name mismatch')
        self.assertTrue(portGroups[0].get_resourceManagerId(
        ) == 'rmId', 'VSwitch portgroup Resource Manager id mismatch')
        self.assertTrue(portGroups[0].get_type(
        ) == 'portgroup_type', 'VSwitch port group type mismatched')
        cost2 = portGroups[0].get_cost()
        self.assertTrue(
            cost2.get_value() == 100, 'PortGroup Cost Value mismatch')
        self.assertTrue(
            cost2.get_units() == 'USD', 'PortGroup Cost units mismatch')
        self.assertTrue(portGroups[1].get_id(
        ) == 'pg-02', 'VSwitch Port Group id mismatch')
        self.assertTrue(portGroups[1].get_name(
        ) == 'pg-02', 'VSwitch Port Group Name mismatch')
        self.assertTrue(portGroups[1].get_resourceManagerId(
        ) == 'rmId', 'VSwitch portgroup Resource Manager id mismatch')
        self.assertTrue(portGroups[1].get_type(
        ) == 'portgroup_type', 'VSwitch port group type mismatched')
        subnetId = virtualswitches[0].get_subnetIds()
        self.assertTrue(
            subnetId[0] == 'subnet-02', 'Virtual Switch subnet id mismatch')
        self.assertTrue(virtualswitches[0].get_networkInterfaces(
        )[0] == '1', 'Virtual Switch network INterfaces mismatch')

    def test_virtual_switch_delete(self):
        virtualswitch = VirtualSwitch()
        virtualswitch.id = 'VS1'
        virtualswitch.switchType = 'switch'

        portGroup = PortGroup()
        portGroup.set_id('pg-01')
        portGroup.set_name('pg-01')
        portGroup.set_resourceManagerId('rmId')
        portGroup.set_type('portgroup_type')
        virtualswitch.add_portGroups(portGroup)
        api.virtual_switch_save(self.admin_context, virtualswitch)

        # virtualswitchs = api.virtual_switch_get_by_ids([virtualswitch.id])

        api.virtual_switch_delete_by_ids(self.admin_context,
                                         [virtualswitch.id])
        virtualswitchs = \
            api.virtual_switch_get_by_ids(self.admin_context,
                                          [virtualswitch.id])
        self.assertTrue(virtualswitchs is None or len(virtualswitchs)
                        == 0, 'switch not deleted')

    def test_virtual_switch_delete_none(self):
        self.assertTrue(api.virtual_switch_delete_by_ids(self.admin_context,
                        None) is None, 'No virtual switch should be deleted')

    def test_virtual_switch_save_throw_exception(self):
        self.assertRaises(Exception, api.virtual_switch_save,
                          self.admin_context, VirtualSwitch())

    def test_virtual_switch_get_ids_exc(self):
        self.mox.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mox.ReplayAll()
        self.assertRaises(Exception, api.virtual_switch_get_by_ids,
                          self.admin_context, ['test1'])

    def test_virtual_switch_get_all_throw_exception(self):
        self.mox.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mox.ReplayAll()
        self.assertRaises(Exception, api.virtual_switch_get_all,
                          self.admin_context)

    def test_virtual_switch_delete_throw_exception(self):
        self.mox.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mox.ReplayAll()
        self.assertRaises(Exception, api.virtual_switch_delete_by_ids,
                          self.admin_context, ['test1'])

    def test_virtual_switch_get_all_by_filters_throw_exception(self):
        self.mox.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mox.ReplayAll()
        self.assertRaises(Exception,
                          api.virtual_switch_get_all_by_filters,
                          self.admin_context, {}, 'id', 'asc')

    def test_virtual_switch_get_all_by_filters(self):
        # Create VirtualSwitches
        switch_ids = ('SW1', 'SW2')
        switch_names = ('name1', 'name2')
        for i in range(len(switch_ids)):
            self.__create_virtual_switch(
                id=switch_ids[i], name=switch_names[i])
        # Query with filter
        filters = {'name': switch_names[1]}
        switches = api.virtual_switch_get_all_by_filters(
            self.admin_context, filters,
            'id', DbConstants.ORDER_ASC)
        self.assert_(switches is not None)
        self.assert_(len(switches) == 1)
        self.assert_(switches[0] is not None)
        self.assert_(switches[0].id == switch_ids[1])

    def test_virtual_switch_get_all_by_filters_deleted(self):
        # Create VirtualSwitches
        switch_ids = ('SW1', 'SW2')
        switch_names = ('name1', 'name2')
        for i in range(len(switch_ids)):
            self.__create_virtual_switch(
                id=switch_ids[i], name=switch_names[i])
        # Delete one switch
        api.virtual_switch_delete_by_ids(self.admin_context, [switch_ids[0]])
        # Query with filter
        filters = {'deleted': 'true'}
        switches = api.virtual_switch_get_all_by_filters(
            self.admin_context, filters,
            'id', DbConstants.ORDER_ASC)
        self.assert_(switches is not None)
        self.assert_(len(switches) == 1)
        self.assert_(switches[0] is not None)
        self.assert_(switches[0].id == switch_ids[0])

    def test_virtual_switch_get_all_by_filters_not_deleted(self):
        # Create VirtualSwitches
        switch_ids = ('SW1', 'SW2')
        switch_names = ('name1', 'name2')
        for i in range(len(switch_ids)):
            self.__create_virtual_switch(
                id=switch_ids[i], name=switch_names[i])
        # Delete one switch
        api.virtual_switch_delete_by_ids(self.admin_context, [switch_ids[0]])
        # Query with filter
        filters = {'deleted': False}
        switches = api.virtual_switch_get_all_by_filters(
            self.admin_context, filters,
            'id', DbConstants.ORDER_ASC)
        self.assert_(switches is not None)
        self.assert_(len(switches) == 1)
        self.assert_(switches[0] is not None)
        self.assert_(switches[0].id == switch_ids[1])

    def test_virtual_switch_get_all_by_filters_changessince(self):
        # Create VirtualSwitches
        switch_ids = ('SW1', 'SW2', 'SW3')
        switch_names = ('name1', 'name2', 'name3')
        for i in range(len(switch_ids)):
            self.__create_virtual_switch(
                id=switch_ids[i], name=switch_names[i])
        created_time = long(time.time() * 1000L)
        # Wait for 1 sec and update second switch and delete third switch
        time.sleep(1)
        second_switch = api.virtual_switch_get_by_ids(
            self.admin_context, [switch_ids[1]])[0]
        second_switch.name = 'New name'
        api.virtual_switch_save(self.admin_context, second_switch)
        api.virtual_switch_delete_by_ids(self.admin_context, [switch_ids[2]])
        # Query with filter
        expected_updated_ids = [switch_ids[1], switch_ids[2]]
        filters = {'changes-since': created_time}
        switches = api.virtual_switch_get_all_by_filters(
            self.admin_context, filters,
            None, None)
        self.assert_(switches is not None)
        self.assert_(len(switches) == 2)
        for switch in switches:
            self.assert_(switch is not None)
            self.assert_(switch.id in expected_updated_ids)

    def test_virtual_switch_get_all_by_filters_sort_asc(self):
        # Create VirtualSwitches
        switch_ids = ('SW1', 'SW2')
        switch_names = ('name1', 'name2')
        for i in range(len(switch_ids)):
            self.__create_virtual_switch(
                id=switch_ids[i], name=switch_names[i])
        # Query with sort
        switches = api.virtual_switch_get_all_by_filters(
            self.admin_context, None,
            'name', DbConstants.ORDER_ASC)
        self.assert_(switches is not None)
        self.assert_(len(switches) == 2)
        self.assert_(switches[0] is not None)
        self.assert_(switches[0].id == switch_ids[0])
        self.assert_(switches[1] is not None)
        self.assert_(switches[1].id == switch_ids[1])

    def test_virtual_switch_get_all_by_filters_sort_desc(self):
        # Create VirtualSwitches
        switch_ids = ('SW1', 'SW2')
        switch_names = ('name1', 'name2')
        for i in range(len(switch_ids)):
            self.__create_virtual_switch(
                id=switch_ids[i], name=switch_names[i])
        # Query with sort
        switches = api.virtual_switch_get_all_by_filters(
            self.admin_context, {'name': switch_names},
            'name', DbConstants.ORDER_DESC)
        self.assert_(switches is not None)
        self.assert_(len(switches) == 2)
        self.assert_(switches[0] is not None)
        self.assert_(switches[0].id == switch_ids[1])
        self.assert_(switches[1] is not None)
        self.assert_(switches[1].id == switch_ids[0])

    def test_virtual_switch_get_all_by_filters_contains(self):
        # Create VirtualSwitches
        switch_ids = ('SW1', 'SW2', 'SW3')
        switch_names = ('name1', 'name2', 'name3')
        switch_net_intfs = (['vnet1'], ['vnet1', 'vnet3'],
                            ['vnet3'])
        for i in range(len(switch_ids)):
            self.__create_virtual_switch(
                id=switch_ids[i], name=switch_names[i],
                networkInterfaces=switch_net_intfs[i])
        # Query with sort
        switches = api.virtual_switch_get_all_by_filters(
            self.admin_context, {
                'networkInterfaces': 'vnet1'},
            'id', DbConstants.ORDER_ASC)
        self.assert_(switches is not None)
        self.assert_(len(switches) == 2)
        self.assert_(switches[0] is not None)
        self.assert_(switches[0].id == switch_ids[0])
        self.assert_(switches[1] is not None)
        self.assert_(switches[1].id == switch_ids[1])

    def test_virtual_switch_multiple_save(self):
        """Test case to test the modification of
        VirtualSwitch along with Subnet"""
        virtualswitch = VirtualSwitch()
        virtualswitch.id = 'VS1'
        virtualswitch.switchType = 'switch'
        subnet_id_lst = ["subnet_1", "subnet_2"]
        'Add one subnet'
        self.__create_subnet(id=subnet_id_lst[0], name=subnet_id_lst[0])
        virtualswitch.set_subnetIds(subnet_id_lst)
        api.virtual_switch_save(self.admin_context, virtualswitch)

        'Update the virtual switch'
        virtualswitch.switchType = 'switchUpdated'
        'Add second subnet'
        self.__create_subnet(id=subnet_id_lst[1], name=subnet_id_lst[1])
        api.virtual_switch_save(self.admin_context, virtualswitch)
        virtualswitches = api.virtual_switch_get_by_ids(
            self.admin_context, [virtualswitch.id])

        self.assertFalse(
            virtualswitches is None, 'VirtualSwitch  all returned a list')
        self.assertTrue(
            virtualswitches[0].id == 'VS1', 'Virtual Switch id mismatch')
        self.assertTrue(virtualswitches[0].switchType == 'switchUpdated',
                        'Virtual Switch type mismatch')
        self.assertTrue(len(virtualswitches[0].subnetIds) >= 0,
                        'Virtual Switch - subnetIds does not exist')
        self.assertTrue(virtualswitches[0].subnetIds[0] in subnet_id_lst,
                        'Virtual Switch - subnetIds is not api output')
        self.assertTrue(virtualswitches[0].subnetIds[1] in subnet_id_lst,
                        'Virtual Switch - subnetIds is not api output')

    def test_timestamp_columns(self):
        """
            Test the time stamp columns createEpoch,
            modifiedEpoch and deletedEpoch
        """
        virSw1 = VirtualSwitch()
        virSw1.set_id('VS1_VH1')
        portGrp1 = PortGroup()
        portGrp1.set_id('PG1_VH1')
        virSw1.add_portGroups(portGrp1)
        # Check for createEpoch
        epoch_before = utils.get_current_epoch_ms()
        api.virtual_switch_save(self.admin_context, virSw1)
        epoch_after = utils.get_current_epoch_ms()
        virsw_queried = api.virtual_switch_get_by_ids(
            self.admin_context, [virSw1.get_id()])[0]
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after, virsw_queried.get_createEpoch()))
        for pg in virsw_queried.get_portGroups():
            self.assert_(test_utils.is_timestamp_between(
                epoch_before, epoch_after, pg.get_createEpoch()))
        # Check for lastModifiedEpoch after modifying switch
        virsw_modified = virsw_queried
        test_utils.unset_timestamp_fields(virsw_modified)
        virsw_modified.set_name('changed_name')
        epoch_before = utils.get_current_epoch_ms()
        api.virtual_switch_save(self.admin_context, virsw_modified)
        epoch_after = utils.get_current_epoch_ms()
        virsw_queried = api.virtual_switch_get_by_ids(
            self.admin_context, [virSw1.get_id()])[0]
        self.assert_(virsw_modified.get_createEpoch(
        ) == virsw_queried.get_createEpoch())
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after, virsw_queried.get_lastModifiedEpoch()))
        for pg in virsw_queried.get_portGroups():
            self.assert_(virsw_modified.get_portGroups()[0].get_createEpoch()
                         == pg.get_createEpoch())
            self.assert_(test_utils.is_timestamp_between(
                epoch_before, epoch_after, pg.get_lastModifiedEpoch()))
        # Check for createdEpoch after adding portgroup to switch
        virsw_modified = virsw_queried
        test_utils.unset_timestamp_fields(virsw_modified)
        portGrp2 = PortGroup()
        portGrp2.set_id('PG2_VH1')
        virsw_modified.add_portGroups(portGrp2)
        epoch_before = utils.get_current_epoch_ms()
        api.virtual_switch_save(self.admin_context, virsw_modified)
        epoch_after = utils.get_current_epoch_ms()
        virsw_queried = api.virtual_switch_get_by_ids(
            self.admin_context, [virSw1.get_id()])[0]
        self.assert_(virsw_modified.get_createEpoch(
        ) == virsw_queried.get_createEpoch())
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after, virsw_queried.get_lastModifiedEpoch()))
        for pg in virsw_queried.get_portGroups():
            if pg.get_id() == portGrp2.get_id():
                self.assert_(test_utils.is_timestamp_between(
                    epoch_before, epoch_after, pg.get_createEpoch()))
            else:
                self.assert_(test_utils.is_timestamp_between(
                    epoch_before, epoch_after, pg.get_lastModifiedEpoch()))
