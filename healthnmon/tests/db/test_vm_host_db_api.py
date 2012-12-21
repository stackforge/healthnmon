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
from healthnmon.resourcemodel.healthnmonResourceModel import VmHost, \
    Vm, HostMountPoint, StorageVolume, VirtualSwitch, PortGroup, Cost, \
    VmGlobalSettings
from healthnmon.tests.db import test
import mox
from nova.db.sqlalchemy import session as db_session
from nova.context import get_admin_context
from healthnmon.constants import DbConstants
import time
from healthnmon import utils
from healthnmon.tests import utils as test_utils


class VmHostDbApiTestCase(test.TestCase):

    def setUp(self):
        super(VmHostDbApiTestCase, self).setUp()
        self.mock = mox.Mox()
        self.admin_context = get_admin_context()

    def tearDown(self):
        super(VmHostDbApiTestCase, self).tearDown()
        self.mock.stubs.UnsetAll()

    def __create_vm_host(self, **kwargs):
        vmhost = VmHost()
        if kwargs is not None:
            for field in kwargs:
                setattr(vmhost, field, kwargs[field])
        healthnmon_db_api.vm_host_save(self.admin_context, vmhost)
        return vmhost

    def __create_vm(self, **kwargs):
        vm = Vm()
        if kwargs is not None:
            for field in kwargs:
                setattr(vm, field, kwargs[field])
        return vm

    def __save(self, vmhost, *vms):
        healthnmon_db_api.vm_host_save(self.admin_context, vmhost)
        if vms:
            for vm in vms:
                healthnmon_db_api.vm_save(self.admin_context, vm)

    def test_vm_host_save(self):
        host_id = 'VH1'
        vmhost = VmHost()
        vmhost.id = host_id

        vSwitch = VirtualSwitch()
        vSwitch.set_id('vSwitch-01')
        vSwitch.set_name('vSwitch-01')
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
        vmhost.add_virtualSwitches(vSwitch)
        vmhost.add_portGroups(portGroup)
        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost)
        vmhosts = \
            healthnmon_db_api.vm_host_get_by_ids(get_admin_context(),
                                                 [host_id])
        self.assertFalse(vmhosts is None,
                         'Host get by id returned a none list')
        self.assertTrue(len(vmhosts) > 0,
                        'Host get by id returned invalid number of list'
                        )
        self.assertTrue(
            len(vmhosts[0].get_virtualSwitches()) > 0,
            'Host get by virtual switch returned invalid number of list')
        self.assertTrue(
            len(vmhosts[0].get_portGroups()) > 0,
            'Host get by port group returned invalid number of list')
        self.assertTrue(vmhosts[0].id == host_id)

    def test_vm_host_save_update(self):
        host_id = 'VH1'
        vmhost = VmHost()
        vmhost.id = host_id

        vSwitch = VirtualSwitch()
        vSwitch.set_id('vSwitch-01')
        vSwitch.set_name('vSwitch-01')
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
        vmhost.add_virtualSwitches(vSwitch)
        vmhost.add_portGroups(portGroup)
        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost)
        vmhosts = \
            healthnmon_db_api.vm_host_get_by_ids(get_admin_context(),
                                                 [host_id])
        self.assertFalse(vmhosts is None,
                         'Host get by id returned a none list')
        self.assertTrue(len(vmhosts) > 0,
                        'Host get by id returned invalid number of list'
                        )
        self.assertTrue(
            len(vmhosts[0].get_virtualSwitches()) > 0,
            'Host get by virtual switch returned invalid number of list')
        self.assertTrue(
            len(vmhosts[0].get_portGroups()) > 0,
            'Host get by port group returned invalid number of list')
        self.assertTrue(vmhosts[0].id == host_id)

    def test_vm_host_save_update_with_new_vSwitch(self):
        host_id = 'VH1'
        vmhost = VmHost()
        vmhost.id = host_id

        vSwitch = VirtualSwitch()
        vSwitch.set_id('vSwitch-01')
        vSwitch.set_name('vSwitch-01')
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
        vmhost.add_virtualSwitches(vSwitch)
        vmhost.add_portGroups(portGroup)
        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost)

        vSwitch_new = VirtualSwitch()
        vSwitch_new.set_id('vSwitch-02')
        vSwitch_new.set_name('vSwitch-02')
        vSwitch_new.set_resourceManagerId('rmId')
        vSwitch_new.set_switchType('vSwitch')

        portGroup_new = PortGroup()
        portGroup_new.set_id('pg-02')
        portGroup_new.set_name('pg-02')
        portGroup_new.set_resourceManagerId('rmId')
        portGroup_new.set_type('portgroup_type')
        vSwitch.add_portGroups(portGroup_new)
        vmhost.add_virtualSwitches(vSwitch_new)
        vmhost.add_portGroups(portGroup_new)
        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost)

        vmhosts = \
            healthnmon_db_api.vm_host_get_by_ids(get_admin_context(),
                                                 [host_id])
        self.assertFalse(vmhosts is None,
                         'Host get by id returned a none list')
        self.assertTrue(len(vmhosts) > 0,
                        'Host get by id returned invalid number of list'
                        )
        self.assertTrue(
            len(vmhosts[0].get_virtualSwitches()) > 0,
            'Host get by virtual switch returned invalid number of list')
        self.assertTrue(
            len(vmhosts[0].get_portGroups()) > 0,
            'Host get by port group returned invalid number of list')
        self.assertTrue(vmhosts[0].id == host_id)

    def test_vm_host_get_all(self):
        '''
        Inserts more than one host with vms and storage volumes.
        Also validates the data retrieved from the vmhost, vm, storage volumes.
        '''
        vmhost = VmHost()
        vmhost.id = 'VH1-id'
        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost)
        vmhost = VmHost()
        vmhost.id = 'VH2-id'
        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost)
        vm = Vm()
        vm.id = 'VM1-id'
        vm.set_vmHostId('VH1-id')
        vmGlobalSettings = VmGlobalSettings()
        vmGlobalSettings.set_id(vm.id)
        vmGlobalSettings.set_autoStartAction('autoStartAction')
        vmGlobalSettings.set_autoStopAction('autoStopAction')
        vm.set_vmGlobalSettings(vmGlobalSettings)
        healthnmon_db_api.vm_save(get_admin_context(), vm)
        mntPnt = HostMountPoint()
        mntPnt.set_vmHostId('VH1-id')
        mntPnt.set_path('/path')
        volume = StorageVolume()
        sv_id = 'SV1-id'
        volume.set_id(sv_id)
        volume.add_mountPoints(mntPnt)
        healthnmon_db_api.storage_volume_save(get_admin_context(), volume)

        vmhosts = healthnmon_db_api.vm_host_get_all(get_admin_context())
        self.assertFalse(vmhosts is None,
                         'vm_host_get_all returned a None')
        self.assertTrue(
            len(vmhosts) == 2,
            'vm_host_get_all does not returned expected number of hosts')
        self.assertEqual(vmhosts[0].get_id(),
                         'VH1-id', "VMHost id is not same")
        self.assertEqual(vmhosts[1].get_id(),
                         'VH2-id', "VMHost id is not same")
        vmlist = vmhosts[0].get_virtualMachineIds()
        self.assertFalse(vmlist is None,
                         "virtual machines from the host returned None")
        self.assertTrue(
            len(vmlist) == 1,
            "length of virtual machines list is not returned as expected")
        self.assertTrue(vm.id in vmlist,
                        "VmId is not in host")

        vms = healthnmon_db_api.vm_get_by_ids(get_admin_context(), ['VM1-id'])
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

        svlist = vmhosts[0].get_storageVolumeIds()
        self.assertFalse(svlist is None,
                         "Storage Volumes from the host returned None")
        self.assertTrue(
            len(svlist) >= 1,
            "length of storage volumes list is not returned as expected")
        self.assertTrue(sv_id in svlist,
                        "Storage Volume Id is not host")

        storagevolumes = \
            healthnmon_db_api.storage_volume_get_by_ids(get_admin_context(),
                                                        ['SV1-id'])
        self.assertFalse(storagevolumes is None,
                         'Storage volume get by id returned a none list')
        self.assertTrue(
            len(storagevolumes) > 0,
            'Storage volume get by id returned invalid number of list')
        self.assertEquals(storagevolumes[0].id,
                          'SV1-id', "Storage volume id is not same")
        hostMountPoints = storagevolumes[0].get_mountPoints()
        self.assertEquals(hostMountPoints[0].get_path(),
                          '/path', "Host mount point path is not same")
        self.assertEquals(
            hostMountPoints[0].get_vmHostId(),
            'VH1-id', "VmHost id is not same for storage volumes")

    def test_vm_host_get_by_id(self):
        host_id = 'VH1'
        vmhost = VmHost()
        vmhost.id = host_id
        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost)
        vm = Vm()
        vm.id = 'VM11'
        vm.set_vmHostId(host_id)
        healthnmon_db_api.vm_save(get_admin_context(), vm)
        mntPnt = HostMountPoint()
        mntPnt.set_vmHostId(host_id)
        mntPnt.set_path('/path')
        volume = StorageVolume()
        volume.set_id('SV11')
        volume.add_mountPoints(mntPnt)
        healthnmon_db_api.storage_volume_save(get_admin_context(),
                                              volume)

        vmhosts = \
            healthnmon_db_api.vm_host_get_by_ids(get_admin_context(),
                                                 [host_id])
        self.assertFalse(vmhosts is None,
                         'Host get by id returned a none list')
        self.assertTrue(len(vmhosts) > 0,
                        'Host get by id returned invalid number of list'
                        )
        self.assertTrue(vmhosts[0].id == host_id)

    def test_vm_host_get_by_id_for_vm(self):
        host_id = 'VH1'
        vmhost = VmHost()
        vmhost.id = host_id
        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost)
        vm = Vm()
        vm.id = 'VM11'
        vm.set_vmHostId(host_id)
        healthnmon_db_api.vm_save(get_admin_context(), vm)
        vmhosts = \
            healthnmon_db_api.vm_host_get_by_ids(get_admin_context(),
                                                 [host_id])
        self.assertFalse(vmhosts is None,
                         'Host get by id returned a none list')
        self.assertTrue(len(vmhosts) > 0,
                        'Host get by id returned invalid number of list'
                        )
        self.assertTrue(vmhosts[0].id == host_id)
        vmids = vmhosts[0].get_virtualMachineIds()
        self.assert_(vmids is not None)
        self.assert_(len(vmids) == 1)
        self.assert_(vm.id in vmids)
        healthnmon_db_api.vm_delete_by_ids(get_admin_context(), [vm.id])
        vmhosts = \
            healthnmon_db_api.vm_host_get_by_ids(get_admin_context(),
                                                 [host_id])
        self.assertTrue(vmhosts[0].id == host_id)
        vmids = vmhosts[0].get_virtualMachineIds()
        self.assert_((vmids is None) or (len(vmids) == 0))

    def test_vm_host_get_all_for_vm(self):
        host_id = 'VH1'
        vmhost = VmHost()
        vmhost.id = host_id
        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost)
        vm = Vm()
        vm.id = 'VM11'
        vm.set_vmHostId(host_id)
        healthnmon_db_api.vm_save(get_admin_context(), vm)
        vmhosts = \
            healthnmon_db_api.vm_host_get_all(get_admin_context())
        self.assertFalse(vmhosts is None,
                         'Host get by id returned a none list')
        self.assertTrue(len(vmhosts) > 0,
                        'Host get by id returned invalid number of list'
                        )
        self.assertTrue(vmhosts[0].id == host_id)
        vmids = vmhosts[0].get_virtualMachineIds()
        self.assert_(vmids is not None)
        self.assert_(len(vmids) == 1)
        self.assert_(vm.id in vmids)
        healthnmon_db_api.vm_delete_by_ids(get_admin_context(), [vm.id])
        vmhosts = \
            healthnmon_db_api.vm_host_get_all(get_admin_context())
        self.assertTrue(vmhosts[0].id == host_id)
        vmids = vmhosts[0].get_virtualMachineIds()
        self.assert_((vmids is None) or (len(vmids) == 0))

    def test_vm_host_get_by_id_for_sv(self):
        host_id = 'VH1'
        vmhost = VmHost()
        vmhost.id = host_id
        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost)
        mntPnt = HostMountPoint()
        mntPnt.set_vmHostId(host_id)
        mntPnt.set_path('/path')
        volume = StorageVolume()
        volume.set_id('SV11')
        volume.add_mountPoints(mntPnt)
        healthnmon_db_api.storage_volume_save(get_admin_context(),
                                              volume)

        vmhosts = \
            healthnmon_db_api.vm_host_get_by_ids(get_admin_context(),
                                                 [host_id])
        self.assertFalse(vmhosts is None,
                         'Host get by id returned a none list')
        self.assertTrue(len(vmhosts) > 0,
                        'Host get by id returned invalid number of list'
                        )
        self.assertTrue(vmhosts[0].id == host_id)
        svlist = vmhosts[0].get_storageVolumeIds()
        self.assert_(svlist is not None)
        self.assert_(len(svlist) == 1)
        self.assert_(volume.get_id() in svlist)

        healthnmon_db_api.storage_volume_delete_by_ids(
            get_admin_context(), [volume.get_id()])
        vmhosts = \
            healthnmon_db_api.vm_host_get_by_ids(get_admin_context(),
                                                 [host_id])
        self.assertTrue(vmhosts[0].id == host_id)
        svids = vmhosts[0].get_storageVolumeIds()
        self.assert_((svids is None) or (len(svids) == 0))

    def test_vm_host_get_all_for_sv(self):
        host_id = 'VH1'
        vmhost = VmHost()
        vmhost.id = host_id
        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost)
        mntPnt = HostMountPoint()
        mntPnt.set_vmHostId(host_id)
        mntPnt.set_path('/path')
        volume = StorageVolume()
        volume.set_id('SV11')
        volume.add_mountPoints(mntPnt)
        healthnmon_db_api.storage_volume_save(get_admin_context(),
                                              volume)

        vmhosts = \
            healthnmon_db_api.vm_host_get_all(get_admin_context())
        self.assertFalse(vmhosts is None,
                         'Host get by id returned a none list')
        self.assertTrue(len(vmhosts) > 0,
                        'Host get by id returned invalid number of list'
                        )
        self.assertTrue(vmhosts[0].id == host_id)
        svlist = vmhosts[0].get_storageVolumeIds()
        self.assert_(svlist is not None)
        self.assert_(len(svlist) == 1)
        self.assert_(volume.get_id() in svlist)

        healthnmon_db_api.storage_volume_delete_by_ids(
            get_admin_context(), [volume.get_id()])
        vmhosts = \
            healthnmon_db_api.vm_host_get_all(get_admin_context())
        self.assertTrue(vmhosts[0].id == host_id)
        svids = vmhosts[0].get_storageVolumeIds()
        self.assert_((svids is None) or (len(svids) == 0))

    def test_vm_host_delete(self):
        vmhost_id = 'VH1'
        vmhost = VmHost()
        vmhost.id = vmhost_id
        vSwitch = VirtualSwitch()
        vSwitch.set_id('vSwitch-01')
        vSwitch.set_name('vSwitch-01')
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
        vmhost.add_virtualSwitches(vSwitch)
        vmhost.add_portGroups(portGroup)
        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost)

        vmhost2 = VmHost()
        vmhost2.set_id('VH2')
        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost2)

        storage = StorageVolume()
        storage.set_id('sv-01')
        storage.set_name('storage-01')
        storage.set_resourceManagerId('rmId')
        storage.set_size(1234)
        storage.set_free(2345)
        storage.set_vmfsVolume(True)
        storage.set_shared(True)
        storage.set_assignedServerCount(1)
        storage.set_volumeType('VMFS')
        storage.set_volumeId('101')

        hostMount1 = HostMountPoint()
        hostMount1.set_path('test_path1')
        hostMount1.set_vmHostId('VH1')
        storage.add_mountPoints(hostMount1)
        hostMount2 = HostMountPoint()
        hostMount2.set_path('test_path2')
        hostMount2.set_vmHostId('VH2')
        storage.add_mountPoints(hostMount2)
        healthnmon_db_api.storage_volume_save(get_admin_context(),
                                              storage)

        vm = Vm()
        vm.set_id('vm-01')
        vm.set_name('vm-01')
        vm.set_vmHostId('VH1')
        healthnmon_db_api.vm_save(get_admin_context(), vm)

        vmhosts = \
            healthnmon_db_api.vm_host_get_by_ids(get_admin_context(),
                                                 [vmhost_id])
        self.assertFalse(vmhosts is None,
                         'host get by id returned a none list')
        self.assertTrue(len(vmhosts) > 0,
                        'host get by id returned invalid number of list'
                        )

        healthnmon_db_api.vm_host_delete_by_ids(get_admin_context(),
                                                [vmhost_id])

        vmhosts = \
            healthnmon_db_api.vm_host_get_by_ids(get_admin_context(),
                                                 [vmhost_id])
        self.assertTrue(vmhosts is None or len(vmhosts) == 0,
                        'host not deleted')

    def test_vm_host_save_none(self):
        '''
        check the vm_host_save api with none object
        '''
        vmhost = VmHost()
        vmhost.id = 'VH1-id'
        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost)
        vmhosts = healthnmon_db_api.vm_host_get_all(get_admin_context())
        self.assertFalse(vmhosts is None, 'vm_host_get_all returned a None')
        self.assertTrue(
            len(vmhosts) == 1,
            'vm_host_get_all does not returned expected number of hosts')
        #Now tries to put None object in the db
        healthnmon_db_api.vm_host_save(get_admin_context(), None)
        #Again tries to retrieve the vmhost from db and
        #check it is same as before
        vmhosts = healthnmon_db_api.vm_host_get_all(get_admin_context())
        self.assertFalse(vmhosts is None, 'vm_host_get_all returned a None')
        self.assertTrue(
            len(vmhosts) == 1,
            'vm_host_get_all does not returned expected number of hosts')

    def test_vm_host_get_by_id_none(self):
        '''
        Check the vm_host_get_by_ids by passing the None as id
        '''
        vmHost = healthnmon_db_api.vm_host_get_by_ids(get_admin_context(),
                                                      None)
        self.assertTrue(vmHost is None,
                        "Vmhost retrived from the none object is not none")

    def test_vm_host_delete_none(self):
        '''
        Check the vm_host_delete_by_ids by passing None as id
        '''
        vmhost = VmHost()
        vmhost.id = 'VH1-id'
        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost)
        vmhosts = healthnmon_db_api.vm_host_get_all(get_admin_context())
        self.assertFalse(vmhosts is None, 'vm_host_get_all returned a None')
        self.assertTrue(
            len(vmhosts) == 1,
            'vm_host_get_all does not returned expected number of hosts')
        #Now call the delete api by passing the id as None
        healthnmon_db_api.vm_host_delete_by_ids(get_admin_context(), None)
        #Again try to retrieve the vmhost and check whether its intact
        vmhosts = healthnmon_db_api.vm_host_get_all(get_admin_context())
        self.assertFalse(vmhosts is None,
                         'vm_host_get_all returned a None')
        self.assertTrue(
            len(vmhosts) == 1,
            'vm_host_get_all does not returned expected number of hosts')

    def test_vm_host_save_throw_exception(self):
        self.assertRaises(Exception, healthnmon_db_api.vm_host_save,
                          get_admin_context(), VmHost())

    def test_vm_host_get_ids_throw_exception(self):
        self.mock.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mock.ReplayAll()
        self.assertRaises(Exception,
                          healthnmon_db_api.vm_host_get_by_ids,
                          get_admin_context(), ['host1'])

    def test_vm_host_get_all_throw_exception(self):
        self.mock.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mock.ReplayAll()
        self.assertRaises(Exception, healthnmon_db_api.vm_host_get_all,
                          get_admin_context())

    def test_vm_host_delete_throw_exception(self):
        self.mock.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mock.ReplayAll()
        self.assertRaises(Exception,
                          healthnmon_db_api.vm_host_delete_by_ids,
                          get_admin_context(), ['test1'])

    def test_vm_host_get_all_by_filters_throw_exception(self):
        self.mock.StubOutWithMock(db_session, 'get_session')
        db_session.get_session().AndRaise(Exception())
        self.mock.ReplayAll()
        self.assertRaises(Exception,
                          healthnmon_db_api.vm_host_get_all_by_filters,
                          get_admin_context(), {}, 'id', 'asc')

    def test_vm_host_get_all_by_filters(self):
        # Create VmHosts
        host_ids = ('VH1', 'VH2')
        host_names = ('name1', 'name2')
        for i in range(len(host_ids)):
            self.__create_vm_host(id=host_ids[i], name=host_names[i])
        # Query with filter
        filters = {'name': host_names[1]}
        vmhosts = healthnmon_db_api.vm_host_get_all_by_filters(
            self.admin_context, filters,
            'id', DbConstants.ORDER_ASC)
        self.assert_(vmhosts is not None)
        self.assert_(len(vmhosts) == 1)
        self.assert_(vmhosts[0] is not None)
        self.assert_(vmhosts[0].id == host_ids[1])

    def test_vm_host_get_all_by_filters_deleted(self):
        # Create VmHosts
        host_ids = ('VH1', 'VH2')
        host_names = ('name1', 'name2')
        for i in range(len(host_ids)):
            self.__create_vm_host(id=host_ids[i], name=host_names[i])
        # Delete one host
        healthnmon_db_api.vm_host_delete_by_ids(
            self.admin_context, [host_ids[0]])
        # Query with filter
        filters = {'deleted': 'true'}
        vmhosts = healthnmon_db_api.vm_host_get_all_by_filters(
            self.admin_context, filters,
            'id', DbConstants.ORDER_ASC)
        self.assert_(vmhosts is not None)
        self.assert_(len(vmhosts) == 1)
        self.assert_(vmhosts[0] is not None)
        self.assert_(vmhosts[0].id == host_ids[0])

    def test_vm_host_get_all_by_filters_not_deleted(self):
        # Create VmHosts
        host_ids = ('VH1', 'VH2')
        host_names = ('name1', 'name2')
        for i in range(len(host_ids)):
            self.__create_vm_host(id=host_ids[i], name=host_names[i])
        # Delete one host
        healthnmon_db_api.vm_host_delete_by_ids(
            self.admin_context, [host_ids[0]])
        # Query with filter
        filters = {'deleted': False}
        vmhosts = healthnmon_db_api.vm_host_get_all_by_filters(
            self.admin_context, filters,
            'id', DbConstants.ORDER_ASC)
        self.assert_(vmhosts is not None)
        self.assert_(len(vmhosts) == 1)
        self.assert_(vmhosts[0] is not None)
        self.assert_(vmhosts[0].id == host_ids[1])

    def test_vm_host_get_all_by_filters_changessince(self):
        # Create VmHosts
        host_ids = ('VH1', 'VH2', 'VH3')
        host_names = ('name1', 'name2', 'name3')
        for i in range(len(host_ids)):
            self.__create_vm_host(id=host_ids[i], name=host_names[i])
        created_time = long(time.time() * 1000L)
        # Wait for 1 sec and update second host and delete third host
        time.sleep(1)
        second_host = healthnmon_db_api.vm_host_get_by_ids(
            self.admin_context, [host_ids[1]])[0]
        second_host.name = 'New name'
        healthnmon_db_api.vm_host_save(self.admin_context, second_host)
        healthnmon_db_api.vm_host_delete_by_ids(
            self.admin_context, [host_ids[2]])
        # Query with filter
        expected_updated_ids = [host_ids[1], host_ids[2]]
        filters = {'changes-since': created_time}
        vmhosts = healthnmon_db_api.vm_host_get_all_by_filters(
            self.admin_context, filters,
            None, None)
        self.assert_(vmhosts is not None)
        self.assert_(len(vmhosts) == 2)
        for host in vmhosts:
            self.assert_(host is not None)
            self.assert_(host.id in expected_updated_ids)

    def test_vm_host_get_all_by_filters_sort_asc(self):
        # Create VmHosts
        host_ids = ('VH1', 'VH2')
        host_names = ('name1', 'name2')
        for i in range(len(host_ids)):
            self.__create_vm_host(id=host_ids[i], name=host_names[i])
        # Query with sort
        vmhosts = healthnmon_db_api.vm_host_get_all_by_filters(
            self.admin_context, None,
            'name', DbConstants.ORDER_ASC)
        self.assert_(vmhosts is not None)
        self.assert_(len(vmhosts) == 2)
        self.assert_(vmhosts[0] is not None)
        self.assert_(vmhosts[0].id == host_ids[0])
        self.assert_(vmhosts[1] is not None)
        self.assert_(vmhosts[1].id == host_ids[1])

    def test_vm_host_get_all_by_filters_sort_desc(self):
        # Create VmHosts
        host_ids = ('VH1', 'VH2')
        host_names = ('name1', 'name2')
        for i in range(len(host_ids)):
            self.__create_vm_host(id=host_ids[i], name=host_names[i])
        # Query with sort
        vmhosts = healthnmon_db_api.vm_host_get_all_by_filters(
            self.admin_context, {'name': host_names},
            'name', DbConstants.ORDER_DESC)
        self.assert_(vmhosts is not None)
        self.assert_(len(vmhosts) == 2)
        self.assert_(vmhosts[0] is not None)
        self.assert_(vmhosts[0].id == host_ids[1])
        self.assert_(vmhosts[1] is not None)
        self.assert_(vmhosts[1].id == host_ids[0])

#
#        Unit tests for defect fix DE126: Healthnmon reports bogus VM
#        guest count values
#
    def _setup_host(self):
        vmhost = self.__create_vm_host(id='1', name='host-1')
        vm_01 = self.__create_vm(id='u23lksd-32342-324l-23423',
                                 name='instance001',
                                 vmHostId='1')
        vm_02 = self.__create_vm(id='u23lksd-32342-324l-demo',
                                 name='instance002',
                                 vmHostId='1')
        return (vmhost, vm_01, vm_02)

    def test_deleted_vm(self):
        """ Test if vmhost get all by filters lists deleted virtual machines
        """
        vmhost, vm_01, vm_02 = self._setup_host()
        vm_01.deleted = True
        self.__save(vmhost, vm_01, vm_02)
        hosts = healthnmon_db_api.vm_host_get_all_by_filters(
            self.admin_context,
            None,
            None,
            None)
        self.assertEquals(hosts[0].get_virtualMachineIds(),
                          ['u23lksd-32342-324l-demo'])
        # Delete second VM
        vm_02.deleted = True
        self.__save(vmhost, vm_01, vm_02)
        hosts = healthnmon_db_api.vm_host_get_all_by_filters(
            self.admin_context,
            None,
            None,
            None)
        self.assertEquals(hosts[0].get_virtualMachineIds(), [])

    def test_vm_not_deleted(self):
        """ Test if vmhost get all by filters lists virtual machines which
            have deleted flag set to false or None.
        """
        vmhost, vm_01, vm_02 = self._setup_host()
        vm_01.deleted = False
        vm_02.deleted = None
        self.__save(vmhost, vm_01, vm_02)
        hosts = healthnmon_db_api.vm_host_get_all_by_filters(
            self.admin_context,
            None,
            None,
            None)
        self.assertEquals(
            hosts[0].get_virtualMachineIds(),
            ['u23lksd-32342-324l-23423', 'u23lksd-32342-324l-demo'])

    def test_deleted_vm_host(self):
        """ Test if vmhost get all by filters lists deleted virtual machines
            if the vmhost was deleted.
        """
        vmhost, vm_01, vm_02 = self._setup_host()
        self.__save(vmhost, vm_01, vm_02)
        healthnmon_db_api.vm_host_delete_by_ids(self.admin_context, vmhost.id)
        self.assertEqual(
            healthnmon_db_api.vm_get_all_by_filters(self.admin_context,
                                                    {'id': vm_01.id},
                                                    None,
                                                    None)[0].deleted,
            True, 'Delete vm host and assert if VM is deleted')

    def test_inconsistent_vmhost(self):
        """ Test if vmhost get all by filters lists deleted virtual machines
            if an inconsistent vmhost was deleted.
        """
        vmhost, vm_01, vm_02 = self._setup_host()
        vmhost.virtualMachineIds = ['a', 'b']
        self.__save(vmhost, vm_01, vm_02)
        healthnmon_db_api.vm_host_delete_by_ids(self.admin_context, vmhost.id)
        self.assertEqual(
            healthnmon_db_api.vm_get_all_by_filters(self.admin_context,
                                                    {'deleted': 'true'},
                                                    None,
                                                    None)[0].deleted,
            True, 'Delete inconsistent vm host and assert if VM is deleted')

    def test_timestamp_columns(self):
        """
            Test the time stamp columns createEpoch,
            modifiedEpoch and deletedEpoch
        """
        vmhost = VmHost()
        vmhost.set_id('VH1')
        virSw1 = VirtualSwitch()
        virSw1.set_id('VS1_VH1')
        portGrp1 = PortGroup()
        portGrp1.set_id('PG1_VH1')
        virSw1.add_portGroups(portGrp1)
        vmhost.add_virtualSwitches(virSw1)
        vmhost.add_portGroups(portGrp1)
        # Check for createEpoch
        epoch_before = utils.get_current_epoch_ms()
        healthnmon_db_api.vm_host_save(self.admin_context, vmhost)
        epoch_after = utils.get_current_epoch_ms()
        vmhost_queried = healthnmon_db_api.vm_host_get_by_ids(
            self.admin_context, [vmhost.get_id()])[0]
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after, vmhost_queried.get_createEpoch()))
        for virSw in vmhost_queried.get_virtualSwitches():
            self.assert_(test_utils.is_timestamp_between(
                epoch_before, epoch_after, virSw.get_createEpoch()))
            for pg in virSw.get_portGroups():
                self.assert_(test_utils.is_timestamp_between(
                    epoch_before, epoch_after, pg.get_createEpoch()))
        # Check for lastModifiedEpoch after modifying host
        vmhost_modified = vmhost_queried
        test_utils.unset_timestamp_fields(vmhost_modified)
        vmhost_modified.set_name('changed_name')
        epoch_before = utils.get_current_epoch_ms()
        healthnmon_db_api.vm_host_save(self.admin_context, vmhost_modified)
        epoch_after = utils.get_current_epoch_ms()
        vmhost_queried = healthnmon_db_api.vm_host_get_by_ids(
            self.admin_context, [vmhost.get_id()])[0]
        self.assert_(vmhost_modified.get_createEpoch(
        ) == vmhost_queried.get_createEpoch())
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after, vmhost_queried.get_lastModifiedEpoch()))
        for virSw in vmhost_queried.get_virtualSwitches():
            self.assert_(test_utils.is_timestamp_between(
                epoch_before, epoch_after, virSw.get_lastModifiedEpoch()))
            for pg in virSw.get_portGroups():
                self.assert_(test_utils.is_timestamp_between(
                    epoch_before, epoch_after, pg.get_lastModifiedEpoch()))
        # Check for createdEpoch after adding switch and portgroup to host
        vmhost_modified = vmhost_queried
        test_utils.unset_timestamp_fields(vmhost_modified)
        virSw2 = VirtualSwitch()
        virSw2.set_id('VS2_VH1')
        portGrp2 = PortGroup()
        portGrp2.set_id('PG2_VH1')
        virSw2.add_portGroups(portGrp2)
        vmhost_modified.add_virtualSwitches(virSw2)
        vmhost_modified.add_portGroups(portGrp2)
        epoch_before = utils.get_current_epoch_ms()
        healthnmon_db_api.vm_host_save(self.admin_context, vmhost_modified)
        epoch_after = utils.get_current_epoch_ms()
        vmhost_queried = healthnmon_db_api.vm_host_get_by_ids(
            self.admin_context, [vmhost.get_id()])[0]
        self.assert_(vmhost_modified.get_createEpoch(
        ) == vmhost_queried.get_createEpoch())
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after, vmhost_queried.get_lastModifiedEpoch()))
        for virSw in vmhost_queried.get_virtualSwitches():
            if virSw.get_id() == virSw2.get_id():
                self.assert_(test_utils.is_timestamp_between(
                    epoch_before, epoch_after, virSw.get_createEpoch()))
            else:
                self.assert_(test_utils.is_timestamp_between(
                    epoch_before, epoch_after, virSw.get_lastModifiedEpoch()))
            for pg in virSw.get_portGroups():
                if pg.get_id() == portGrp2.get_id():
                    self.assert_(test_utils.is_timestamp_between(
                        epoch_before, epoch_after, pg.get_createEpoch()))
                else:
                    self.assert_(test_utils.is_timestamp_between(
                        epoch_before, epoch_after, pg.get_lastModifiedEpoch()))
        # Check for deletedEpoch
        epoch_before = utils.get_current_epoch_ms()
        healthnmon_db_api.vm_host_delete_by_ids(
            self.admin_context, [vmhost_queried.get_id()])
        epoch_after = utils.get_current_epoch_ms()
        deleted_host = healthnmon_db_api.vm_host_get_all_by_filters(
            self.admin_context,
            {"id": vmhost_queried.get_id()}, None, None)[0]
        self.assertTrue(deleted_host.get_deleted())
        self.assert_(test_utils.is_timestamp_between(
            epoch_before, epoch_after, deleted_host.get_deletedEpoch()))
        deleted_switches = healthnmon_db_api.\
            virtual_switch_get_all_by_filters(self.admin_context,
                                              {"id": (virSw1.get_id(),
                                                      virSw2.get_id())},
                                              None, None)
        for deleted_switch in deleted_switches:
            self.assertTrue(deleted_switch.get_deleted())
            self.assert_(test_utils.is_timestamp_between(
                epoch_before, epoch_after, deleted_switch.get_deletedEpoch()))
            for deleted_portgrp in deleted_switch.get_portGroups():
                self.assertTrue(deleted_portgrp.get_deleted())
                self.assert_(test_utils.is_timestamp_between(
                    epoch_before, epoch_after,
                    deleted_portgrp.get_deletedEpoch()))

    def _create_cost(self):
        cost1 = Cost()
        cost1.set_value(100)
        cost1.set_units('USD')
        return cost1

    def _create_port_group(self, pg_id):
        portGroup = PortGroup()
        portGroup.set_id(pg_id)
        portGroup.set_name(pg_id)
        portGroup.set_resourceManagerId('rmId')
        portGroup.set_type('portgroup_type')
        return portGroup

    def _create_switch(self, switch_id):
        vSwitch = VirtualSwitch()
        vSwitch.set_id(switch_id)
        vSwitch.set_name(switch_id)
        vSwitch.set_resourceManagerId('rmId')
        vSwitch.set_switchType('vSwitch')
        return vSwitch

    def test_vmhost_save_modify_delete_with_vSwitch_pGroup(self):
        """Test case for filter deleted virtual switch and port group
        1. Create host with 2 virtual switch and port groups.
        2. Assert for the above point.
        3. Save VmHost by removing one virtualwitch and one port group.
        4. Assert for deleted virtual switch and port group.
        5. Delete the host.
        6. Use filter_by api to assert for deleted host,
        virtual switch and port group.
        """
        "Test for  points 1 and 2"
        host_id = 'VH1'
        vmhost = VmHost()
        vmhost.id = host_id
        cost = self._create_cost()
        vSwitch1 = self._create_switch(host_id + '_vSwitch-01')
        vSwitch1.set_cost(cost)
        portGroup1 = self._create_port_group(host_id + '_pGroup-01')
        portGroup1.set_cost(cost)
        vSwitch1.add_portGroups(portGroup1)
        vmhost.add_virtualSwitches(vSwitch1)
        vmhost.add_portGroups(portGroup1)

        "Add the second vswitch and portgroup"
        vSwitch2 = self._create_switch(host_id + '_vSwitch-02')
        vSwitch2.set_cost(cost)
        portGroup2 = self._create_port_group(host_id + '_pGroup-02')
        portGroup2.set_cost(cost)
        vSwitch2.add_portGroups(portGroup2)
        vmhost.add_virtualSwitches(vSwitch2)
        vmhost.add_portGroups(portGroup2)

        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost)
        vmhosts = healthnmon_db_api.vm_host_get_by_ids(
            get_admin_context(), [host_id])
        self.assertFalse(
            vmhosts is None, 'Host get by id returned a none list')
        self.assertTrue(
            len(vmhosts[0].get_virtualSwitches()) > 0,
            'Host get by virtual switch returned invalid number of list')
        vss = vmhosts[0].get_virtualSwitches()
        vs_ids = []
        for vs in vss:
            vs_ids.append(vs.get_id())
        self.assertTrue(
            vSwitch1.get_id() in vs_ids,
            "Added virtual switch1 does not appears in the host api")
        self.assertTrue(
            vSwitch2.get_id() in vs_ids,
            "Added virtual switch2 does not appears in the host api")
        pgs = vmhosts[0].get_portGroups()
        pg_ids = []
        for pg in pgs:
            pg_ids.append(pg.get_id())
        self.assertTrue(portGroup1.get_id(
        ) in pg_ids, "Added port group1 does not appears in the host api")
        self.assertTrue(portGroup2.get_id(
        ) in pg_ids, "Added port group2 does not appears in the host api")

        # Points 3 and 4 - Remove the second vswitch and
        # portgroup from the vmhost and the save the vmhost"
        vmhost = VmHost()
        vmhost.id = host_id
        cost = self._create_cost()
        vSwitch = self._create_switch(host_id + '_vSwitch-01')
        vSwitch.set_cost(cost)
        portGroup = self._create_port_group(host_id + '_pGroup-01')
        portGroup.set_cost(cost)
        vSwitch.add_portGroups(portGroup)
        vmhost.add_virtualSwitches(vSwitch)
        vmhost.add_portGroups(portGroup)
        healthnmon_db_api.vm_host_save(get_admin_context(), vmhost)

        vmhosts = healthnmon_db_api.vm_host_get_by_ids(
            get_admin_context(), [host_id])
        self.assertFalse(
            vmhosts is None, 'Host get by id returned a none list')
        vss = vmhosts[0].get_virtualSwitches()
        vs_ids = []
        for vs in vss:
            vs_ids.append(vs.get_id())
        self.assertTrue(
            vSwitch.get_id() in vs_ids,
            "Modified virtual switch1 not appearing in the host api")
        self.assertTrue(vSwitch2.get_id() not in vs_ids,
                        "Deleted virtual switch2 appears in the host api")
        pgs = vmhosts[0].get_portGroups()
        pg_ids = []
        for pg in pgs:
            pg_ids.append(pg.get_id())
        self.assertTrue(portGroup.get_id(
        ) in pg_ids, "Modified port group1 not appearing in the host api")
        self.assertTrue(portGroup2.get_id(
        ) not in pg_ids, "Deleted port group2 appears in the host api")

        # Points 5 and 6 - Delete the host and
        # assert for deletion using filter-by api"
        filters = {'id': host_id, 'deleted': 'true'}
        healthnmon_db_api.vm_host_delete_by_ids(get_admin_context(), [host_id])
        del_vmhosts = healthnmon_db_api.vm_host_get_all_by_filters(
            get_admin_context(), filters, 'id', 'asc')
        self.assertFalse(
            del_vmhosts is None, 'Host get by filters returned a none list')
        vss = del_vmhosts[0].get_virtualSwitches()
        vs_ids = []
        for vs in vss:
            vs_ids.append(vs.get_id())
        self.assertTrue(
            vSwitch1.get_id() in vs_ids,
            "Deleted virtual switch1 not appearing in the host filter api")
        self.assertTrue(
            vSwitch2.get_id() in vs_ids,
            "Deleted virtual switch2 not appears in the host filter api")
        pgs = del_vmhosts[0].get_portGroups()
        pg_ids = []
        for pg in pgs:
            pg_ids.append(pg.get_id())
        self.assertTrue(
            portGroup1.get_id() in pg_ids,
            "Deleted port group1 not appearing in the host filter api")
        self.assertTrue(
            portGroup2.get_id() in pg_ids,
            "Deleted port group2 not appears in the host filter api")
