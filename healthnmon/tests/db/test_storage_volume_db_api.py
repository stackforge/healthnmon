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
from healthnmon.resourcemodel.healthnmonResourceModel import StorageVolume
from healthnmon.resourcemodel.healthnmonResourceModel import Vm, VmDisk
from healthnmon.resourcemodel.healthnmonResourceModel import VmGlobalSettings
from healthnmon.tests.db import test
from nova.db.sqlalchemy import session
import mox
from nova.context import get_admin_context
from healthnmon.constants import DbConstants
import time
from healthnmon import utils
from healthnmon.tests import utils as test_utils


class StoragevolumeDbApiTestCase(test.TestCase):

    def setUp(self):
        super(StoragevolumeDbApiTestCase, self).setUp()
        self.mock = mox.Mox()
        self.admin_context = get_admin_context()

    def tearDown(self):
        super(StoragevolumeDbApiTestCase, self).tearDown()
        self.mock.stubs.UnsetAll()

    def __create_volume(self, **kwargs):
        vol = StorageVolume()
        if kwargs is not None:
            for field in kwargs:
                setattr(vol, field, kwargs[field])
        healthnmon_db_api.storage_volume_save(self.admin_context, vol)
        return vol

    def test_storagevolume_save(self):
        storagevolume = StorageVolume()
        storagevolume.id = 'SV1'
        healthnmon_db_api.storage_volume_save(self.admin_context,
                                              storagevolume)
        healthnmon_db_api.storage_volume_save(self.admin_context,
                                              storagevolume)

    def test_storagevolume_get_all(self):
        storagevolume = StorageVolume()
        storagevolume.id = 'SV1'
        healthnmon_db_api.storage_volume_save(self.admin_context,
                                              storagevolume)
        storagevolume = StorageVolume()
        storagevolume.id = 'SV2'
        healthnmon_db_api.storage_volume_save(self.admin_context,
                                              storagevolume)
        storagevolumes = \
            healthnmon_db_api.storage_volume_get_all(self.admin_context)
        self.assertFalse(storagevolumes is None,
                         'storage volume all returned a none list')
        self.assertTrue(len(storagevolumes) == 2,
                        'storage volume all returned invalid number of list'
                        )
        self.assertTrue(
            storagevolumes[0].id == 'SV1', 'Storage volume id mismatch')
        self.assertTrue(
            storagevolumes[1].id == 'SV2', 'Storage volume id mismatch')

    def test_storagevolume_get_by_id(self):
        storagevolume_id = 'SV1'
        storagevolume = StorageVolume()
        storagevolume.id = storagevolume_id
        healthnmon_db_api.storage_volume_save(self.admin_context,
                                              storagevolume)

        storagevolumes = \
            healthnmon_db_api.storage_volume_get_by_ids(self.admin_context,
                                                        [storagevolume_id])
        self.assertFalse(storagevolumes is None,
                         'storage volume get by id returned a none list'
                         )
        self.assertTrue(
            len(storagevolumes) > 0,
            'storage volume get by id returned invalid number of list')
        self.assertTrue(storagevolumes[0].id == 'SV1')

    def test_storagevolume_delete(self):
        storagevolume = StorageVolume()
        storagevolume_id = 'SV1'
        storagevolume.id = storagevolume_id
        vm = Vm()
        vm.set_id('vm-01')
        vmGlobalSettings = VmGlobalSettings()
        vmGlobalSettings.set_id('vm_01')
        vm.set_vmGlobalSettings(vmGlobalSettings)
        vmDisk = VmDisk()
        vmDisk.set_id('disk-01')
        vmDisk.set_storageVolumeId(storagevolume_id)
        vm.add_vmDisks(vmDisk)
        vmDisk = VmDisk()
        vmDisk.set_id('disk-02')
        vmDisk.set_storageVolumeId('SV2')
        vm.add_vmDisks(vmDisk)
        healthnmon_db_api.vm_save(self.admin_context, vm)

        healthnmon_db_api.storage_volume_save(self.admin_context,
                                              storagevolume)

        storagevolumes = \
            healthnmon_db_api.storage_volume_get_by_ids(self.admin_context,
                                                        [storagevolume_id])
        self.assertFalse(storagevolumes is None,
                         'storage volume get by id returned a none list'
                         )
        self.assertTrue(
            len(storagevolumes) > 0,
            'storage volume get by id returned invalid number of list')

        healthnmon_db_api.storage_volume_delete_by_ids(self.admin_context,
                                                       [storagevolume_id])

        storagevolumes = \
            healthnmon_db_api.storage_volume_get_by_ids(self.admin_context,
                                                        [storagevolume_id])
        self.assertTrue(storagevolumes is None or len(storagevolumes)
                        == 0, 'Storage volume not deleted')

    def test_storagevolume_save_none(self):
        self.assertTrue(
            healthnmon_db_api.storage_volume_save(
                self.admin_context, None) is None,
            'The storage volume should save nothing')

    def test_storagevolume_get_by_id_none(self):
        storageVolumes = healthnmon_db_api.storage_volume_get_by_ids(
            self.admin_context,
            None)
        self.assertTrue(
            storageVolumes is None, 'Storage Volumes should be an empty list')

    def test_storagevolume_delete_none(self):
        self.assertTrue(
            healthnmon_db_api.storage_volume_delete_by_ids(
                self.admin_context,
                None) is None, 'Storage Volumes should be an empty list')

    def test_storagevolume_save_throw_exception(self):
        self.assertRaises(Exception,
                          healthnmon_db_api.storage_volume_save,
                          self.admin_context, StorageVolume())

    def test_storage_get_ids_throw_exception(self):
        self.mock.StubOutWithMock(session, 'get_session')
        session.get_session().AndRaise(Exception())
        self.mock.ReplayAll()
        self.assertRaises(Exception,
                          healthnmon_db_api.storage_volume_get_by_ids,
                          self.admin_context, ['test1'])

    def test_storage_get_all_throw_exception(self):
        self.mock.StubOutWithMock(session, 'get_session')
        session.get_session().AndRaise(Exception())
        self.mock.ReplayAll()
        self.assertRaises(Exception,
                          healthnmon_db_api.storage_volume_get_all,
                          self.admin_context)

    def test_storage_delete_throw_exception(self):
        self.mock.StubOutWithMock(session, 'get_session')
        session.get_session().AndRaise(Exception())
        self.mock.ReplayAll()
        self.assertRaises(Exception,
                          healthnmon_db_api.storage_volume_delete_by_ids,
                          self.admin_context, ['test1'])

    def test_storage_volume_get_all_by_filters_throw_exception(self):
        self.mock.StubOutWithMock(session, 'get_session')
        session.get_session().AndRaise(Exception())
        self.mock.ReplayAll()
        self.assertRaises(Exception,
                          healthnmon_db_api.storage_volume_get_all_by_filters,
                          self.admin_context, {}, 'id', 'asc')

    def test_storage_volume_get_all_by_filters(self):
        # Create StorageVolumes
        vol_ids = ('V1', 'V2')
        vol_names = ('name1', 'name2')
        for i in range(len(vol_ids)):
            self.__create_volume(id=vol_ids[i], name=vol_names[i])
        # Query with filter
        filters = {'name': vol_names[1]}
        vols = healthnmon_db_api.storage_volume_get_all_by_filters(
            self.admin_context, filters,
            'id', DbConstants.ORDER_ASC)
        self.assert_(vols is not None)
        self.assert_(len(vols) == 1)
        self.assert_(vols[0] is not None)
        self.assert_(vols[0].id == vol_ids[1])

    def test_storage_volume_get_all_by_filters_deleted(self):
        # Create StorageVolumes
        vol_ids = ('V1', 'V2')
        vol_names = ('name1', 'name2')
        for i in range(len(vol_ids)):
            self.__create_volume(id=vol_ids[i], name=vol_names[i])
        # Delete one vol
        healthnmon_db_api.storage_volume_delete_by_ids(
            self.admin_context, [vol_ids[0]])
        # Query with filter
        filters = {'deleted': 'true'}
        vols = healthnmon_db_api.storage_volume_get_all_by_filters(
            self.admin_context, filters,
            'id', DbConstants.ORDER_ASC)
        self.assert_(vols is not None)
        self.assert_(len(vols) == 1)
        self.assert_(vols[0] is not None)
        self.assert_(vols[0].id == vol_ids[0])

    def test_storage_volume_get_all_by_filters_not_deleted(self):
        # Create StorageVolumes
        vol_ids = ('V1', 'V2')
        vol_names = ('name1', 'name2')
        for i in range(len(vol_ids)):
            self.__create_volume(id=vol_ids[i], name=vol_names[i])
        # Delete one vol
        healthnmon_db_api.storage_volume_delete_by_ids(
            self.admin_context, [vol_ids[0]])
        # Query with filter
        filters = {'deleted': 'false'}
        vols = healthnmon_db_api.storage_volume_get_all_by_filters(
            self.admin_context, filters,
            'id', DbConstants.ORDER_ASC)
        print "vols::", vols[0].id
        self.assert_(vols is not None)
        self.assert_(len(vols) == 1)
        self.assert_(vols[0] is not None)
        self.assert_(vols[0].id == vol_ids[1])

    def test_storage_volume_get_all_by_filters_changessince(self):
        # Create StorageVolumes
        vol_ids = ('V1', 'V2', 'V3')
        vol_names = ('name1', 'name2', 'name3')
        for i in range(len(vol_ids)):
            self.__create_volume(id=vol_ids[i], name=vol_names[i])
        created_time = long(time.time() * 1000L)
        # Wait for 1 sec and update second vol and delete third vol
        time.sleep(1)
        second_vol = healthnmon_db_api.storage_volume_get_by_ids(
            self.admin_context, [vol_ids[1]])[0]
        second_vol.name = 'New name'
        healthnmon_db_api.storage_volume_save(self.admin_context, second_vol)
        healthnmon_db_api.storage_volume_delete_by_ids(
            self.admin_context, [vol_ids[2]])
        # Query with filter
        expected_updated_ids = [vol_ids[1], vol_ids[2]]
        filters = {'changes-since': created_time}
        vols = healthnmon_db_api.storage_volume_get_all_by_filters(
            self.admin_context, filters,
            None, None)
        self.assert_(vols is not None)
        self.assert_(len(vols) == 2)
        for vol in vols:
            self.assert_(vol is not None)
            self.assert_(vol.id in expected_updated_ids)

    def test_storage_volume_get_all_by_filters_sort_asc(self):
        # Create StorageVolumes
        vol_ids = ('V1', 'V2')
        vol_names = ('name1', 'name2')
        for i in range(len(vol_ids)):
            self.__create_volume(id=vol_ids[i], name=vol_names[i])
        # Query with sort
        vols = healthnmon_db_api.storage_volume_get_all_by_filters(
            self.admin_context, None,
            'name', DbConstants.ORDER_ASC)
        self.assert_(vols is not None)
        self.assert_(len(vols) == 2)
        self.assert_(vols[0] is not None)
        self.assert_(vols[0].id == vol_ids[0])
        self.assert_(vols[1] is not None)
        self.assert_(vols[1].id == vol_ids[1])

    def test_storage_volume_get_all_by_filters_sort_desc(self):
        # Create StorageVolumes
        vol_ids = ('V1', 'V2')
        vol_names = ('name1', 'name2')
        for i in range(len(vol_ids)):
            self.__create_volume(id=vol_ids[i], name=vol_names[i])
        # Query with sort
        vols = healthnmon_db_api.storage_volume_get_all_by_filters(
            self.admin_context, {'name': vol_names},
            'name', DbConstants.ORDER_DESC)
        self.assert_(vols is not None)
        self.assert_(len(vols) == 2)
        self.assert_(vols[0] is not None)
        self.assert_(vols[0].id == vol_ids[1])
        self.assert_(vols[1] is not None)
        self.assert_(vols[1].id == vol_ids[0])

    def test_timestamp_columns(self):
        """
            Test the time stamp columns createEpoch,
            modifiedEpoch and deletedEpoch
        """
        vol = StorageVolume()
        vol.set_id('vol-01')
        # Check for createEpoch
        epoch_before = utils.get_current_epoch_ms()
        healthnmon_db_api.storage_volume_save(self.admin_context, vol)
        epoch_after = utils.get_current_epoch_ms()
        vol_queried = healthnmon_db_api.storage_volume_get_by_ids(
            self.admin_context, [vol.get_id()])[0]
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after, vol_queried.get_createEpoch()))
        # Check for lastModifiedEpoch
        vol_modified = vol_queried
        test_utils.unset_timestamp_fields(vol_modified)
        vol_modified.set_name('changed_name')
        epoch_before = utils.get_current_epoch_ms()
        healthnmon_db_api.storage_volume_save(self.admin_context, vol_modified)
        epoch_after = utils.get_current_epoch_ms()
        vol_queried = healthnmon_db_api.storage_volume_get_by_ids(
            self.admin_context, [vol.get_id()])[0]
        self.assert_(
            vol_modified.get_createEpoch() == vol_queried.get_createEpoch())
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after, vol_queried.get_lastModifiedEpoch()))
