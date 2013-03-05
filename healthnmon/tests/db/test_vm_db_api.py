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

from healthnmon.db import api as healthnmon_db_api
from healthnmon.resourcemodel.healthnmonResourceModel import Vm, \
    VmScsiController
from healthnmon.resourcemodel.healthnmonResourceModel import VmNetAdapter
from healthnmon.resourcemodel.healthnmonResourceModel import VmGlobalSettings
from healthnmon import test
from nova.db.sqlalchemy import session as db_session
from nova.context import get_admin_context
from healthnmon.constants import DbConstants, Constants
import time
from healthnmon import utils
from healthnmon.tests import utils as test_utils


class VmDbApiTestCase(test.TestCase):

    def setUp(self):
        super(VmDbApiTestCase, self).setUp()
        # self.mock = mox.Mox()
        self.admin_context = get_admin_context()

    def tearDown(self):
        super(VmDbApiTestCase, self).tearDown()
#        self.mock.stubs.UnsetAll()

    def __create_vm(self, **kwargs):
        vm = Vm()
        if kwargs is not None:
            for field in kwargs:
                setattr(vm, field, kwargs[field])
        healthnmon_db_api.vm_save(self.admin_context, vm)
        return vm

    def test_vm_save(self):
        '''
        Insert a vm object into db and check
        whether we are getting proper values after retrieval
        '''
        vm = Vm()
        vm.id = 'VM1-id'
        vm.name = 'VM1-Name'
        vmScsiController = VmScsiController()
        vmScsiController.set_id('VM_CTRL_1')
        vmScsiController.set_id('some_type')
        vm.add_vmScsiControllers(vmScsiController)
        healthnmon_db_api.vm_save(get_admin_context(), vm)

        vms = healthnmon_db_api.vm_get_by_ids(get_admin_context(), [vm.id])
        self.assertTrue(vms is not None)
        self.assertTrue(len(vms) == 1)
        self.assertEqual(vms[0].get_id(), 'VM1-id', "VM id is not same")
        self.assertEqual(vms[0].get_name(), 'VM1-Name', "VM name is not same")
        self.assert_(len(vms[0].get_vmScsiControllers(
        )) == 1, "vmScsiController len mismatch")
        self.assert_(vms[0].get_vmScsiControllers()[0].get_id(
        ) == vmScsiController.get_id(), "vmScsiController id mismatch")
        self.assert_(vms[0].get_vmScsiControllers()[0].get_type() ==
                     vmScsiController.get_type(),
                     "vmScsiController type mismatch")

    def test_vm_save_update(self):
        '''
        Update an existing object in db
        '''
        vm = Vm()
        vm.id = 'VM1-id'
        healthnmon_db_api.vm_save(get_admin_context(), vm)

        vmGlobalSettings = VmGlobalSettings()
        vmGlobalSettings.set_id(vm.id)
        vmGlobalSettings.set_autoStartAction('autoStartAction')
        vmGlobalSettings.set_autoStopAction('autoStopAction')
        vm.set_vmGlobalSettings(vmGlobalSettings)
        healthnmon_db_api.vm_save(get_admin_context(), vm)

        vms = healthnmon_db_api.vm_get_by_ids(get_admin_context(), [vm.id])
        self.assertTrue(vms is not None)
        self.assertTrue(len(vms) == 1)
        vm = vms[0]
        self.assertEqual(vm.get_id(), 'VM1-id', "VM id is not same")
        vmGlobalSets = vm.get_vmGlobalSettings()
        self.assertTrue(vmGlobalSets is not None)
        self.assertEqual(vmGlobalSets.get_id(), 'VM1-id', "VM id is not same")
        self.assertEqual(vmGlobalSets.get_autoStartAction(),
                         'autoStartAction', "autoStartAction is not same")
        self.assertEqual(vmGlobalSets.get_autoStopAction(),
                         'autoStopAction', "autoStopAction is not same")

    def test_vm_get_all(self):
        '''
        Inserts more than one vm object and
        try to get them all and validates the values
        '''
        vm = Vm()
        vm.id = 'VM1-id'
        vm.name = 'VM1-Name'
        healthnmon_db_api.vm_save(get_admin_context(), vm)

        vm = Vm()
        vm.id = 'VM2-id'
        vm.name = 'VM2-Name'
        healthnmon_db_api.vm_save(get_admin_context(), vm)

        vms = healthnmon_db_api.vm_get_all(get_admin_context())
        self.assertFalse(vms is None, 'vm_get_all returned None')
        self.assertTrue(len(vms) == 2,
                        'vm_get_all does not returned expected number of vms')
        self.assertEqual(vms[0].get_id(), 'VM1-id', "VM id is not same")
        self.assertEqual(vms[1].get_id(), 'VM2-id', "VM id is not same")
        self.assertEqual(vms[0].get_name(), 'VM1-Name', "VM Name is not same")
        self.assertEqual(vms[1].get_name(), 'VM2-Name', "VM Name is not same")

    def test_vm_get_by_id(self):
        vm_id = 'VM1'
        vm = Vm()
        vm.id = vm_id
        healthnmon_db_api.vm_save(get_admin_context(), vm)

        vms = healthnmon_db_api.vm_get_by_ids(get_admin_context(),
                                              [vm_id])
        self.assertFalse(vms is None,
                         'VM get by id returned a none list')
        self.assertTrue(len(vms) > 0,
                        'VM get by id returned invalid number of list')
        self.assertTrue(vms[0].id == 'VM1')

    def test_vm_delete(self):
        vm = Vm()
        vm_id = 'VM1'
        vm.id = vm_id
        vmGlobalSettings = VmGlobalSettings()
        vmGlobalSettings.set_id(vm_id)
        vm.set_vmGlobalSettings(vmGlobalSettings)
        healthnmon_db_api.vm_save(get_admin_context(), vm)

        vms = healthnmon_db_api.vm_get_by_ids(get_admin_context(),
                                              [vm_id])
        self.assertFalse(vms is None,
                         'VM get by id returned a none list')
        self.assertTrue(len(vms) > 0,
                        'VM get by id returned invalid number of list')

        healthnmon_db_api.vm_delete_by_ids(get_admin_context(), [vm_id])

        vms = healthnmon_db_api.vm_get_by_ids(get_admin_context(),
                                              [vm_id])
        self.assertTrue(vms is None or len(vms) == 0, 'VM not deleted')

    def test_vm_netadpater_save(self):
        vm = Vm()
        vm.id = 'VM1'
        vmNetAdapter = VmNetAdapter()
        vmNetAdapter.set_id('netAdapter-01')
        vmNetAdapter.set_name('netAdapter-01')
        vmNetAdapter.set_addressType('assigned')
        vmNetAdapter.set_adapterType('E1000')
        vmNetAdapter.set_switchType('vSwitch')
        vmNetAdapter.set_macAddress('00:50:56:81:1c:d0')
        vmNetAdapter.add_ipAddresses('1.1.1.1')
        vmNetAdapter.set_networkName('br100')
        vmNetAdapter.set_vlanId(0)

        vm.add_vmNetAdapters(vmNetAdapter)
        healthnmon_db_api.vm_save(get_admin_context(), vm)
        virual_machines = \
            healthnmon_db_api.vm_get_by_ids(get_admin_context(), ['VM1'
                                                                  ])
        vm_from_db = virual_machines[0]
        netAdapters = vm_from_db.get_vmNetAdapters()
        netAdapter = netAdapters[0]
        self.assertTrue(vmNetAdapter.get_id() == netAdapter.get_id())
        healthnmon_db_api.vm_delete_by_ids(get_admin_context(), [vm.id])

        vms = healthnmon_db_api.vm_get_by_ids(get_admin_context(),
                                              [vm.id])
        self.assertTrue(vms is None or len(vms) == 0, 'VM not deleted')

    def test_vm_save_none(self):
        # Initially insert a vm into db and check the length
        vm = Vm()
        vm.id = 'VM1-id'
        healthnmon_db_api.vm_save(get_admin_context(), vm)
        vms = healthnmon_db_api.vm_get_all(get_admin_context())
        self.assertTrue(vms is not None)
        self.assertTrue(len(vms) == 1)

        # Now try to save the none and check the length is same as previous
        healthnmon_db_api.vm_save(get_admin_context(), None)
        vmsaved = healthnmon_db_api.vm_get_all(get_admin_context())
        self.assertTrue(vmsaved is not None)
        self.assertTrue(len(vmsaved) == 1)

    def test_vm_get_by_id_none(self):

        # Try to get the vm with Id None and check whether it is returning None
        vms = healthnmon_db_api.vm_get_by_ids(get_admin_context(), None)
        self.assertTrue(vms is None)

    def test_vm_delete_none(self):
        # Initially insert a vm into db and check the length
        vm = Vm()
        vm.id = 'VM1-id'
        healthnmon_db_api.vm_save(get_admin_context(), vm)
        vms = healthnmon_db_api.vm_get_all(get_admin_context())
        self.assertTrue(vms is not None)
        self.assertTrue(len(vms) == 1)

        # Now delete the None from db
        healthnmon_db_api.vm_delete_by_ids(get_admin_context(), None)
        vms = healthnmon_db_api.vm_get_all(get_admin_context())
        self.assertTrue(vms is not None)
        self.assertTrue(len(vms) == 1)

    def test_vm_save_throw_exception(self):
        self.assertRaises(Exception, healthnmon_db_api.vm_save,
                          get_admin_context(), Vm())

    def test_vm_get_ids_throw_exception(self):
        self.mox.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mox.ReplayAll()
        self.assertRaises(Exception, healthnmon_db_api.vm_get_by_ids,
                          get_admin_context(), ['test1'])

    def test_vm_get_all_throw_exception(self):
        self.mox.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mox.ReplayAll()
        self.assertRaises(Exception, healthnmon_db_api.vm_get_all,
                          get_admin_context())

    def test_vm_delete_throw_exception(self):
        self.mox.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mox.ReplayAll()
        self.assertRaises(Exception,
                          healthnmon_db_api.vm_delete_by_ids,
                          get_admin_context(), ['test1'])

    def test_vm_get_all_by_filters_throw_exception(self):
        self.mox.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mox.ReplayAll()
        self.assertRaises(Exception,
                          healthnmon_db_api.vm_get_all_by_filters,
                          get_admin_context(), {}, 'id', 'asc')

    def test_vm_get_all_by_filters(self):
        # Create Vm
        vm_ids = ('VM1', 'VM2')
        vm_names = ('name1', 'name2')
        for i in range(len(vm_ids)):
            self.__create_vm(id=vm_ids[i], name=vm_names[i])
        # Query with filter
        filters = {'name': vm_names[1]}
        vms = healthnmon_db_api.vm_get_all_by_filters(
            self.admin_context, filters,
            'id', DbConstants.ORDER_ASC)
        self.assert_(vms is not None)
        self.assert_(len(vms) == 1)
        self.assert_(vms[0] is not None)
        self.assert_(vms[0].id == vm_ids[1])

    def test_vm_get_all_by_filters_deleted(self):
        # Create Vm
        vm_ids = ('VM1', 'VM2')
        vm_names = ('name1', 'name2')
        for i in range(len(vm_ids)):
            self.__create_vm(id=vm_ids[i], name=vm_names[i])
        # Delete one vm
        healthnmon_db_api.vm_delete_by_ids(self.admin_context, [vm_ids[0]])
        # Query with filter
        filters = {'deleted': 'true'}
        vms = healthnmon_db_api.vm_get_all_by_filters(
            self.admin_context, filters,
            'id', DbConstants.ORDER_ASC)
        self.assert_(vms is not None)
        self.assert_(len(vms) == 1)
        self.assert_(vms[0] is not None)
        self.assert_(vms[0].id == vm_ids[0])

    def test_vm_get_all_by_filters_not_deleted(self):
        # Create Vm
        vm_ids = ('VM1', 'VM2')
        vm_names = ('name1', 'name2')
        for i in range(len(vm_ids)):
            self.__create_vm(id=vm_ids[i], name=vm_names[i])
        # Delete one vm
        healthnmon_db_api.vm_delete_by_ids(self.admin_context, [vm_ids[0]])
        # Query with filter
        filters = {'deleted': False}
        vms = healthnmon_db_api.vm_get_all_by_filters(
            self.admin_context, filters,
            'id', DbConstants.ORDER_ASC)
        self.assert_(vms is not None)
        self.assert_(len(vms) == 1)
        self.assert_(vms[0] is not None)
        self.assert_(vms[0].id == vm_ids[1])

    def test_vm_get_all_by_filters_changessince(self):
        # Create Vm
        vm_ids = ('VM1', 'VM2', 'VM3')
        vm_names = ('name1', 'name2', 'name3')
        for i in range(len(vm_ids)):
            self.__create_vm(id=vm_ids[i], name=vm_names[i])
        created_time = long(time.time() * 1000L)
        # Wait for 1 sec and update second vm and delete third vm
        time.sleep(1)
        second_vm = healthnmon_db_api.vm_get_by_ids(
            self.admin_context, [vm_ids[1]])[0]
        second_vm.name = 'New name'
        healthnmon_db_api.vm_save(self.admin_context, second_vm)
        healthnmon_db_api.vm_delete_by_ids(self.admin_context, [vm_ids[2]])
        # Query with filter
        expected_updated_ids = [vm_ids[1], vm_ids[2]]
        filters = {'changes-since': created_time}
        vms = healthnmon_db_api.vm_get_all_by_filters(
            self.admin_context, filters,
            None, None)
        self.assert_(vms is not None)
        self.assert_(len(vms) == 2)
        for vm in vms:
            self.assert_(vm is not None)
            self.assert_(vm.id in expected_updated_ids)

    def test_vm_get_all_by_filters_sort_asc(self):
        # Create Vm
        vm_ids = ('VM1', 'VM2')
        vm_names = ('name1', 'name2')
        for i in range(len(vm_ids)):
            self.__create_vm(id=vm_ids[i], name=vm_names[i])
        # Query with sort
        vms = healthnmon_db_api.vm_get_all_by_filters(
            self.admin_context, None,
            'name', DbConstants.ORDER_ASC)
        self.assert_(vms is not None)
        self.assert_(len(vms) == 2)
        self.assert_(vms[0] is not None)
        self.assert_(vms[0].id == vm_ids[0])
        self.assert_(vms[1] is not None)
        self.assert_(vms[1].id == vm_ids[1])

    def test_vm_get_all_by_filters_sort_desc(self):
        # Create Vm
        vm_ids = ('VM1', 'VM2')
        vm_names = ('name1', 'name2')
        for i in range(len(vm_ids)):
            self.__create_vm(id=vm_ids[i], name=vm_names[i])
        # Query with sort
        vms = healthnmon_db_api.vm_get_all_by_filters(
            self.admin_context, {'name': vm_names},
            'name', DbConstants.ORDER_DESC)
        self.assert_(vms is not None)
        self.assert_(len(vms) == 2)
        self.assert_(vms[0] is not None)
        self.assert_(vms[0].id == vm_ids[1])
        self.assert_(vms[1] is not None)
        self.assert_(vms[1].id == vm_ids[0])

    def test_timestamp_columns(self):
        """
            Test the time stamp columns createEpoch,
            modifiedEpoch and deletedEpoch
        """
        vm = Vm()
        vm.set_id('VM1')
        # Check for createEpoch
        epoch_before = utils.get_current_epoch_ms()
        healthnmon_db_api.vm_save(self.admin_context, vm)
        epoch_after = utils.get_current_epoch_ms()
        vm_queried = healthnmon_db_api.vm_get_by_ids(
            self.admin_context, [vm.get_id()])[0]
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after, vm_queried.get_createEpoch()))

        # Check for lastModifiedEpoch and createEpoch
        # after adding VmGlobalSettings
        vm_modified = vm_queried
        test_utils.unset_timestamp_fields(vm_modified)
        vmGlobalSettings = VmGlobalSettings()
        vmGlobalSettings.set_id('VMGS1')
        vmGlobalSettings.set_autoStartAction(Constants.AUTO_START_ENABLED)
        vm_modified.set_vmGlobalSettings(vmGlobalSettings)
        epoch_before = utils.get_current_epoch_ms()
        healthnmon_db_api.vm_save(self.admin_context, vm_modified)
        epoch_after = utils.get_current_epoch_ms()
        vm_queried = healthnmon_db_api.vm_get_by_ids(
            self.admin_context, [vm.get_id()])[0]
        self.assert_(
            vm_modified.get_createEpoch() == vm_queried.get_createEpoch())
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after, vm_queried.get_lastModifiedEpoch()))
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after,
            vm_queried.get_vmGlobalSettings().get_createEpoch()))
        # Check for lastModifiedEpoch after modifying vm
        vm_modified = vm_queried
        test_utils.unset_timestamp_fields(vm_modified)
        vm_modified.set_name('changed_name')
        epoch_before = utils.get_current_epoch_ms()
        healthnmon_db_api.vm_save(self.admin_context, vm_modified)
        epoch_after = utils.get_current_epoch_ms()
        vm_queried = healthnmon_db_api.vm_get_by_ids(
            self.admin_context, [vm.get_id()])[0]
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after, vm_queried.get_lastModifiedEpoch()))
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after,
            vm_queried.get_vmGlobalSettings().get_lastModifiedEpoch()))
        self.assert_(
            vm_modified.get_createEpoch() == vm_queried.get_createEpoch())
        self.assert_(vm_modified.get_vmGlobalSettings().get_createEpoch() ==
                     vm_queried.get_vmGlobalSettings().get_createEpoch())
