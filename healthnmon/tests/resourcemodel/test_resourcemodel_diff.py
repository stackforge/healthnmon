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

""" Unit Test Class for testing ResourceModelDiff module """

from nova import test
from healthnmon.resourcemodel.healthnmonResourceModel import StorageVolume, \
    HostMountPoint, Vm, VmDisk, VmHost, VirtualSwitch
from healthnmon.resourcemodel.resourcemodel_diff import ResourceModelDiff
import copy


class ResourceModelDiffTestCase(test.TestCase):

    """ Unit Test Class for testing ResourceModelDiff module """
    update = '_update'
    add = '_add'
    delete = '_delete'

    def setUp(self):
        super(ResourceModelDiffTestCase, self).setUp()

    def tearDown(self):
        super(ResourceModelDiffTestCase, self).tearDown()

    def test_diff_resourcemodel_storagevolume_nochange(self):
        """Unit Test to test for resource model comparison with no change """

        storagevolume = StorageVolume()
        storagevolume.set_id('datastore-112')
        storagevolume.set_name('datastore-112')
        storagevolume.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume.set_size(107105746944)
        storagevolume.set_free(32256294912)
        storagevolume.set_vmfsVolume(False)
        storagevolume.set_shared(False)
        storagevolume.set_assignedServerCount(1)
        storagevolume.set_volumeType('VMFS')
        storagevolume.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )
        hostMountPoint = \
            HostMountPoint(
                '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
                'host-9')
        storagevolume.add_mountPoints(hostMountPoint)

        storagevolume1 = StorageVolume()
        storagevolume1.set_id('datastore-112')
        storagevolume1.set_name('datastore-112')
        storagevolume1.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume1.set_size(107105746944)
        storagevolume1.set_free(32256294912)
        storagevolume1.set_vmfsVolume(False)
        storagevolume1.set_shared(False)
        storagevolume1.set_assignedServerCount(1)
        storagevolume1.set_volumeType('VMFS')
        storagevolume1.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )
        hostMountPoint1 = \
            HostMountPoint(
                '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
                'host-9')
        storagevolume1.add_mountPoints(hostMountPoint1)

        diff = ResourceModelDiff(storagevolume, storagevolume1)
        diff_res = diff.diff_resourcemodel()

        self.assertTrue(len(diff_res) == 0)

    def test_diff_resourcemodel_storagevolume_withupdate(self):
        """Unit Test to test for resource model comparison with some change """

        storagevolume = StorageVolume()
        storagevolume.set_id('datastore-112')
        storagevolume.set_name('datastore-112')
        storagevolume.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume.set_size(107105746944)
        storagevolume.set_free(32256294912)
        storagevolume.set_vmfsVolume(False)
        storagevolume.set_shared(False)
        storagevolume.set_assignedServerCount(1)
        storagevolume.set_volumeType('VMFS')
        storagevolume.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )
        hostMountPoint = \
            HostMountPoint(
                '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
                'host-9')
        storagevolume.add_mountPoints(hostMountPoint)

        storagevolume1 = StorageVolume()
        storagevolume1.set_id('datastore-112')
        storagevolume1.set_name('datastore-112')
        storagevolume1.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume1.set_size(107105746944)
        storagevolume1.set_free(32256294912)
        storagevolume1.set_vmfsVolume(False)
        storagevolume1.set_shared(False)
        storagevolume1.set_assignedServerCount(1)
        storagevolume1.set_volumeType('VMFS')
        storagevolume1.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )
        hostMountPoint1 = \
            HostMountPoint(
                '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
                'host-19')
        storagevolume1.add_mountPoints(hostMountPoint1)

        diff = ResourceModelDiff(storagevolume, storagevolume1)
        diff_res = diff.diff_resourcemodel()
        self.assertTrue(len(diff_res) > 0)
        self.assertTrue(self.update in diff_res)
        mountPoints = 'mountPoints'
        vmHostId = 'vmHostId'
        self.assertTrue(mountPoints in diff_res[self.update])
        self.assertTrue(self.update in diff_res[self.update][mountPoints])
        key = diff_res[self.update][mountPoints][self.update].keys()[0]
        self.assertTrue(self.update in diff_res[self.update][mountPoints][
            self.update][key])
        self.assertTrue(vmHostId in diff_res[self.update][mountPoints][
            self.update][key][self.update])
        self.assertEquals(diff_res[self.update][mountPoints][self.update][
            key][self.update][vmHostId], 'host-19')

    def test_diff_resourcemodel_storagevolume_withupdateadd(self):
        """Unit Test to test for resource model comparison with some change """

        storagevolume = StorageVolume()
        storagevolume.set_id('datastore-112')
        storagevolume.set_name('datastore-112')
        storagevolume.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume.set_size(107105746944)
        storagevolume.set_free(32256294912)
        storagevolume.set_vmfsVolume(False)
        storagevolume.set_shared(False)
        storagevolume.set_assignedServerCount(1)
        storagevolume.set_volumeType('VMFS')
        storagevolume.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )
        hostMountPoint = \
            HostMountPoint(
                '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
                'host-9')
        storagevolume.add_mountPoints(hostMountPoint)

        storagevolume1 = StorageVolume()
        storagevolume1.set_id('datastore-114')
        storagevolume1.set_name('datastore-114')
        storagevolume1.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume1.set_size(107105746944)
        storagevolume1.set_free(32256294912)
        storagevolume1.set_vmfsVolume(False)
        storagevolume1.set_shared(False)
        storagevolume1.set_assignedServerCount(1)
        storagevolume1.set_volumeType('VMFS')
        storagevolume1.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )
        hostMountPoint1 = \
            HostMountPoint(
                '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
                'host-19')
        storagevolume1.add_mountPoints(hostMountPoint1)
        hostMountPoint2 = \
            HostMountPoint(
                '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5dc',
                'host-20')
        storagevolume1.add_mountPoints(hostMountPoint2)

        diff = ResourceModelDiff(storagevolume, storagevolume1)
        diff_res = diff.diff_resourcemodel()
        self.assertTrue(len(diff_res) > 0)

        self.assertTrue(self.update in diff_res)
        mountPoints = 'mountPoints'
        vmHostId = 'vmHostId'

        self.assertTrue(mountPoints in diff_res[self.update])
        self.assertTrue(self.add in diff_res[self.update][mountPoints])

        key = diff_res[self.update][mountPoints][self.add].keys()[0]
        self.assertTrue(isinstance(diff_res[self.update][mountPoints][
                        self.add][key], HostMountPoint))
        addMount = diff_res[self.update][mountPoints][self.add][key]
        self.assertEquals(addMount.vmHostId, 'host-20')
        self.assertEquals(addMount.path,
                          '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5dc')

        self.assertTrue(self.update in diff_res[self.update][mountPoints])
        key1 = diff_res[self.update][mountPoints][self.update].keys()[0]
        self.assertTrue(self.update in diff_res[self.update][mountPoints][
            self.update][key1])
        self.assertTrue(vmHostId in diff_res[self.update][mountPoints][
            self.update][key1][self.update])
        self.assertEquals(diff_res[self.update][mountPoints][self.update][
            key1][self.update][vmHostId], 'host-19')

        self.assertTrue('id' in diff_res[self.update])
        self.assertEquals(diff_res[self.update]['id'], 'datastore-114')

        self.assertTrue('name' in diff_res[self.update])
        self.assertEquals(diff_res[self.update]['name'], 'datastore-114')

    def test_diff_resourcemodel_storagevolume_withdelete(self):
        """Unit Test to test for resource model comparison with some change """

        storagevolume = StorageVolume()
        storagevolume.set_id('datastore-112')
        storagevolume.set_name('datastore-112')
        storagevolume.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume.set_size(107105746944)
        storagevolume.set_free(32256294912)
        storagevolume.set_vmfsVolume(False)
        storagevolume.set_shared(False)
        storagevolume.set_assignedServerCount(1)
        storagevolume.set_volumeType('VMFS')
        storagevolume.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )
        hostMountPoint = \
            HostMountPoint(
                '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
                'host-9')
        storagevolume.add_mountPoints(hostMountPoint)

        storagevolume1 = StorageVolume()
        storagevolume1.set_id('datastore-114')
        storagevolume1.set_name('datastore-114')
        storagevolume1.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume1.set_size(107105746944)
        storagevolume1.set_free(32256294912)
        storagevolume1.set_vmfsVolume(False)
        storagevolume1.set_shared(False)
        storagevolume1.set_assignedServerCount(1)
        storagevolume1.set_volumeType('VMFS')
        storagevolume1.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )

        diff = ResourceModelDiff(storagevolume, storagevolume1)
        diff_res = diff.diff_resourcemodel()
        self.assertTrue(len(diff_res) > 0)
        self.assertTrue(self.update in diff_res)
        mountPoints = 'mountPoints'
        self.assertTrue(mountPoints in diff_res[self.update])
        self.assertTrue(self.delete in diff_res[self.update][mountPoints])

        key = diff_res[self.update][mountPoints][self.delete].keys()[0]
        self.assertTrue(isinstance(diff_res[self.update][mountPoints][
                        self.delete][key], HostMountPoint))
        delMount = diff_res[self.update][mountPoints][self.delete][key]
        self.assertEquals(delMount.vmHostId, 'host-9')
        self.assertEquals(delMount.path,
                          '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db')

        self.assertTrue('id' in diff_res[self.update])
        self.assertEquals(diff_res[self.update]['id'], 'datastore-114')

        self.assertTrue('name' in diff_res[self.update])
        self.assertEquals(diff_res[self.update]['name'], 'datastore-114')

    def test_diff_resourcemodel_vm_withaddupdtedelete(self):
        vm = Vm()
        vm.set_id('vm-01')
        vm.set_name('vm-01')
        disk1 = VmDisk()
        disk1.set_id('disk-01')
        disk1.set_storageVolumeId('datastore-939')
        disk2 = VmDisk()
        disk2.set_id('disk-02')
        disk2.set_storageVolumeId('datastore-439')
        vm.add_vmDisks(disk1)
        vm.add_vmDisks(disk2)
        vm.set_vmHostId('host-329')

        vm1 = Vm()
        vm1.set_id('vm-01')
        vm1.set_name('vm-01')
        disk11 = VmDisk()
        disk11.set_id('disk-01')
        disk11.set_storageVolumeId('datastore-939-999')
        disk21 = VmDisk()
        disk21.set_id('disk-03')
        disk21.set_storageVolumeId('datastore-439-999')
        vm1.add_vmDisks(disk11)
        vm1.add_vmDisks(disk21)
        vm1.set_vmHostId('host-329-999')

        diff = ResourceModelDiff(vm, vm1)
        diff_res = diff.diff_resourcemodel()
        self.assertTrue(len(diff_res) > 0)
        self.assertTrue(self.update in diff_res)
        vmDisks = 'vmDisks'
        self.assertTrue(vmDisks in diff_res[self.update])

        self.assertTrue(self.add in diff_res[self.update][vmDisks])
        self.assertTrue('disk-03' in diff_res[self.update][vmDisks][self.add])
        self.assertTrue(isinstance(diff_res[self.update][vmDisks][self.add][
            'disk-03'], VmDisk))
        addVmdisk = diff_res[self.update][vmDisks][self.add]['disk-03']
        self.assertEquals(addVmdisk.get_storageVolumeId(), 'datastore-439-999')

        self.assertTrue(self.delete in diff_res[self.update][vmDisks])
        self.assertTrue('disk-02' in diff_res[self.update][vmDisks][
            self.delete])
        self.assertTrue(isinstance(diff_res[self.update][vmDisks][
            self.delete]['disk-02'], VmDisk))
        delVmdisk = diff_res[self.update][vmDisks][self.delete]['disk-02']
        self.assertEquals(delVmdisk.get_storageVolumeId(), 'datastore-439')

        self.assertTrue(self.update in diff_res[self.update][vmDisks])
        self.assertTrue('disk-01' in diff_res[self.update][vmDisks][
            self.update])
        self.assertTrue(self.update in diff_res[self.update][vmDisks][
            self.update]['disk-01'])
        self.assertTrue('storageVolumeId' in diff_res[self.update][vmDisks][
            self.update]['disk-01'][self.update])
        self.assertEquals(diff_res[self.update][vmDisks][self.update][
                          'disk-01'][self.update]['storageVolumeId'],
                          'datastore-939-999')

        self.assertTrue('vmHostId' in diff_res[self.update])
        self.assertEquals(diff_res[self.update]['vmHostId'], 'host-329-999')

    # -------------------------------------------
    # Test Cases to test change in dictionary type
    # --------------------------------------------
    def test_diff_resourcemodel_storagevolume_nochange_withDict(self):
        """Unit Test to test for resource model comparison with no change """

        storagevolume = StorageVolume()
        storagevolume.set_id('datastore-112')
        storagevolume.set_name('datastore-112')
        storagevolume.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume.set_size(107105746944)
        storagevolume.set_free(32256294912)
        storagevolume.set_vmfsVolume(False)
        storagevolume.set_shared(False)
        storagevolume.set_assignedServerCount(1)
        storagevolume.set_volumeType('VMFS')
        storagevolume.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )
        hostMountPoint = \
            HostMountPoint(
                {'1': '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
                 '2': 'host-9'})
        storagevolume.add_mountPoints(hostMountPoint)

        storagevolume1 = StorageVolume()
        storagevolume1.set_id('datastore-112')
        storagevolume1.set_name('datastore-112')
        storagevolume1.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume1.set_size(107105746944)
        storagevolume1.set_free(32256294912)
        storagevolume1.set_vmfsVolume(False)
        storagevolume1.set_shared(False)
        storagevolume1.set_assignedServerCount(1)
        storagevolume1.set_volumeType('VMFS')
        storagevolume1.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )
        hostMountPoint1 = \
            HostMountPoint(
                {'1': '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
                 '2': 'host-9'})
        storagevolume1.add_mountPoints(hostMountPoint1)

        diff = ResourceModelDiff(storagevolume, storagevolume1)
        diff_res = diff.diff_resourcemodel()

        self.assertTrue(len(diff_res) == 0)

    def test_diff_resourcemodel_storagevolume_withupdate_withDict(self):
        """Unit Test to test for resource model comparison with some change """

        storagevolume = StorageVolume()
        storagevolume.set_id('datastore-112')
        storagevolume.set_name('datastore-112')
        storagevolume.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume.set_size(107105746944)
        storagevolume.set_free(32256294912)
        storagevolume.set_vmfsVolume(False)
        storagevolume.set_shared(False)
        storagevolume.set_assignedServerCount(1)
        storagevolume.set_volumeType('VMFS')
        storagevolume.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )
        hostMountPoint = \
            HostMountPoint(
                {'1': '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
                 '2': 'host-9'})
        storagevolume.add_mountPoints(hostMountPoint)

        storagevolume1 = StorageVolume()
        storagevolume1.set_id('datastore-112')
        storagevolume1.set_name('datastore-112')
        storagevolume1.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume1.set_size(107105746944)
        storagevolume1.set_free(32256294912)
        storagevolume1.set_vmfsVolume(False)
        storagevolume1.set_shared(False)
        storagevolume1.set_assignedServerCount(1)
        storagevolume1.set_volumeType('VMFS')
        storagevolume1.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )
        hostMountPoint1 = \
            HostMountPoint(
                {'1': '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
                 '2': 'host-19'})
        storagevolume1.add_mountPoints(hostMountPoint1)

        diff = ResourceModelDiff(storagevolume, storagevolume1)
        diff_res = diff.diff_resourcemodel()
        self.assertTrue(len(diff_res) > 0)

        self.assertTrue(self.update in diff_res)
        mountPoints = 'mountPoints'

        self.assertTrue(mountPoints in diff_res[self.update])
        self.assertTrue(self.update in diff_res[self.update][mountPoints])

        key = diff_res[self.update][mountPoints][self.update].keys()[0]

        self.assertTrue(self.update in diff_res[self.update][mountPoints][
            self.update][key])
        self.assertTrue('path' in diff_res[self.update][mountPoints][
            self.update][key][self.update])
        self.assertTrue(self.update in diff_res[self.update][mountPoints][
            self.update][key][self.update]['path'])
        self.assertTrue('2' in diff_res[self.update][mountPoints][
                        self.update][key][self.update]['path'][self.update])
        self.assertEquals(diff_res[self.update][mountPoints][self.update][
            key][self.update]['path'][self.update]['2'], 'host-19')

    def test_diff_resourcemodel_storagevolume_withupdateadd_withDict(self):
        """Unit Test to test for resource model comparison with some change """

        storagevolume = StorageVolume()
        storagevolume.set_id('datastore-112')
        storagevolume.set_name('datastore-112')
        storagevolume.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume.set_size(107105746944)
        storagevolume.set_free(32256294912)
        storagevolume.set_vmfsVolume(False)
        storagevolume.set_shared(False)
        storagevolume.set_assignedServerCount(1)
        storagevolume.set_volumeType('VMFS')
        storagevolume.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )
        hostMountPoint = \
            HostMountPoint(
                {'1': '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
                 '2': 'host-9'})
        storagevolume.add_mountPoints(hostMountPoint)

        storagevolume1 = StorageVolume()
        storagevolume1.set_id('datastore-114')
        storagevolume1.set_name('datastore-114')
        storagevolume1.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume1.set_size(107105746944)
        storagevolume1.set_free(32256294912)
        storagevolume1.set_vmfsVolume(False)
        storagevolume1.set_shared(False)
        storagevolume1.set_assignedServerCount(1)
        storagevolume1.set_volumeType('VMFS')
        storagevolume1.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )
        hostMountPoint1 = \
            HostMountPoint(
                {'1': '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
                 '2': 'host-19'})
        storagevolume1.add_mountPoints(hostMountPoint1)
        hostMountPoint2 = \
            HostMountPoint(
                {'1': '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5dc',
                 '2': 'host-20'})
        storagevolume1.add_mountPoints(hostMountPoint2)

        diff = ResourceModelDiff(storagevolume, storagevolume1)
        diff_res = diff.diff_resourcemodel()
        self.assertTrue(len(diff_res) > 0)

        self.assertTrue(self.update in diff_res)
        mountPoints = 'mountPoints'

        self.assertTrue(mountPoints in diff_res[self.update])
        self.assertTrue(self.update in diff_res[self.update][mountPoints])

        key = diff_res[self.update][mountPoints][self.update].keys()[0]

        self.assertTrue(self.update in diff_res[self.update][mountPoints][
            self.update][key])
        self.assertTrue('path' in diff_res[self.update][mountPoints][
            self.update][key][self.update])
        self.assertTrue(self.update in diff_res[self.update][mountPoints][
            self.update][key][self.update]['path'])
        self.assertTrue('2' in diff_res[self.update][mountPoints][
                        self.update][key][self.update]['path'][self.update])
        self.assertEquals(diff_res[self.update][mountPoints][self.update][
            key][self.update]['path'][self.update]['2'], 'host-19')

        self.assertTrue(self.add in diff_res[self.update][mountPoints])

        key = diff_res[self.update][mountPoints][self.add].keys()[0]
        self.assertTrue(isinstance(diff_res[self.update][mountPoints][
                        self.add][key], HostMountPoint))
        addMount = diff_res[self.update][mountPoints][self.add][key]
        self.assertEquals(
            addMount.pathProp,
            {'1': '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5dc',
             '2': 'host-20'})

        self.assertTrue('id' in diff_res[self.update])
        self.assertEquals(diff_res[self.update]['id'], 'datastore-114')

        self.assertTrue('name' in diff_res[self.update])
        self.assertEquals(diff_res[self.update]['name'], 'datastore-114')

    def test_diff_resourcemodel_storagevolume_withdelete_withDict(self):
        """Unit Test to test for resource model comparison with some change """

        storagevolume = StorageVolume()
        storagevolume.set_id('datastore-112')
        storagevolume.set_name('datastore-112')
        storagevolume.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume.set_size(107105746944)
        storagevolume.set_free(32256294912)
        storagevolume.set_vmfsVolume(False)
        storagevolume.set_shared(False)
        storagevolume.set_assignedServerCount(1)
        storagevolume.set_volumeType('VMFS')
        storagevolume.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )
        hostMountPoint = \
            HostMountPoint(
                {'1': '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
                 '2': 'host-9'})
        storagevolume.add_mountPoints(hostMountPoint)

        storagevolume1 = StorageVolume()
        storagevolume1.set_id('datastore-114')
        storagevolume1.set_name('datastore-114')
        storagevolume1.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume1.set_size(107105746944)
        storagevolume1.set_free(32256294912)
        storagevolume1.set_vmfsVolume(False)
        storagevolume1.set_shared(False)
        storagevolume1.set_assignedServerCount(1)
        storagevolume1.set_volumeType('VMFS')
        storagevolume1.set_volumeId(
            {'1': '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'})

        diff = ResourceModelDiff(storagevolume, storagevolume1)
        diff_res = diff.diff_resourcemodel()
        self.assertTrue(len(diff_res) > 0)

        self.assertTrue(self.update in diff_res)
        mountPoints = 'mountPoints'
        self.assertTrue(mountPoints in diff_res[self.update])
        self.assertTrue(self.delete in diff_res[self.update][mountPoints])

        key = diff_res[self.update][mountPoints][self.delete].keys()[0]
        self.assertTrue(isinstance(diff_res[self.update][mountPoints][
                        self.delete][key], HostMountPoint))
        delMount = diff_res[self.update][mountPoints][self.delete][key]
        self.assertEquals(
            delMount.pathProp,
            {'1': '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
             '2': 'host-9'})

        self.assertTrue('id' in diff_res[self.update])
        self.assertEquals(diff_res[self.update]['id'], 'datastore-114')

        self.assertTrue('name' in diff_res[self.update])
        self.assertEquals(diff_res[self.update]['name'], 'datastore-114')

        self.assertTrue('volumeId' in diff_res[self.update])
        self.assertEquals(
            diff_res[self.update]['volumeId'],
            {'1': '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'})

    def test_diff_resourcemodel_virtualSwitch_withadd(self):
        cachedHost = VmHost()
        cachedHost.id = '1'
        vmhost = VmHost()
        vmhost.id = '1'
        vswitch = VirtualSwitch()
        vswitch.set_id("11")
        vswitch.set_name("vs1")
        vmhost.set_virtualSwitches([vswitch])
        diff = ResourceModelDiff(cachedHost, vmhost)
        diff_res = diff.diff_resourcemodel()
        self.assertTrue(len(diff_res) > 0)
        self.assertTrue(self.update in diff_res)
        virtualSwitches = 'virtualSwitches'
        self.assertTrue(virtualSwitches in diff_res[self.update])
        self.assertTrue(self.add in diff_res[self.update][virtualSwitches])

        key = diff_res[self.update][virtualSwitches][self.add].keys()[0]
        self.assertTrue(isinstance(diff_res[self.update][virtualSwitches][
                        self.add][key], VirtualSwitch))
        addVirSwitch = diff_res[self.update][virtualSwitches][self.add][key]
        self.assertEquals(addVirSwitch.id, '11')
        self.assertEquals(addVirSwitch.name, 'vs1')

    def test_diff_test_diff_resourcemodel_virtualSwitch_withdelete(self):
        cachedHost = VmHost()
        cachedHost.id = '1'
        vswitch = VirtualSwitch()
        vswitch.set_id("11")
        vswitch.set_name("vs1")
        cachedHost.set_virtualSwitches([vswitch])
        vmhost = copy.deepcopy(cachedHost)
        vmhost.get_virtualSwitches().pop()
        diff = ResourceModelDiff(cachedHost, vmhost)
        diff_res = diff.diff_resourcemodel()
        self.assertTrue(len(diff_res) > 0)
        self.assertTrue(self.update in diff_res)
        virtualSwitches = 'virtualSwitches'
        self.assertTrue(virtualSwitches in diff_res[self.update])
        self.assertTrue(self.delete in diff_res[self.update][virtualSwitches])

        key = diff_res[self.update][virtualSwitches][self.delete].keys()[0]
        self.assertTrue(isinstance(diff_res[self.update][virtualSwitches][
                        self.delete][key], VirtualSwitch))
        delVirSwitch = diff_res[self.update][virtualSwitches][self.delete][key]
        self.assertEquals(delVirSwitch.id, '11')
        self.assertEquals(delVirSwitch.name, 'vs1')

    def test_diff_getAllMembers_none(self):
        storagevolume = StorageVolume()
        storagevolume1 = StorageVolume()
        self.mox.StubOutWithMock(StorageVolume, 'get_all_members')
        storagevolume.get_all_members().AndReturn(None)
        storagevolume1.get_all_members().AndReturn(None)
        self.mox.ReplayAll()
        diff = ResourceModelDiff(storagevolume, storagevolume1)
        diff_res = diff.diff_resourcemodel()
        self.assertTrue(len(diff_res) == 0)

    def test_diff_getAllMembers_emptyDict(self):
        storagevolume = StorageVolume()
        storagevolume1 = StorageVolume()
        self.mox.StubOutWithMock(StorageVolume, 'get_all_members')
        storagevolume.get_all_members().AndReturn({})
        storagevolume1.get_all_members().AndReturn({})
        self.mox.ReplayAll()
        diff = ResourceModelDiff(storagevolume, storagevolume1)
        diff_res = diff.diff_resourcemodel()
        self.assertTrue(len(diff_res) == 0)

    def test_diff_differentResources(self):
        storagevolume = StorageVolume()
        vm = Vm()
        diff = ResourceModelDiff(storagevolume, vm)
        diff_res = diff.diff_resourcemodel()
        self.assertTrue(len(diff_res) > 0)

    def test_diff_dict_emptyDict(self):
        storagevolume = StorageVolume()
        hostMountPoint = HostMountPoint({})
        storagevolume.add_mountPoints(hostMountPoint)
        storagevolume1 = StorageVolume()
        hostMountPoint1 = HostMountPoint({})
        storagevolume1.add_mountPoints(hostMountPoint1)
        diff = ResourceModelDiff(storagevolume, storagevolume1)
        diff_res = diff.diff_resourcemodel()
        self.assertTrue(len(diff_res) == 0)

    def test_diff_differentDict(self):
        storagevolume = StorageVolume()
        storagevolume.set_id('datastore-112')
        storagevolume.set_name('datastore-112')
        storagevolume.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume.set_size(107105746944)
        storagevolume.set_free(32256294912)
        storagevolume.set_vmfsVolume(False)
        storagevolume.set_shared(False)
        storagevolume.set_assignedServerCount(1)
        storagevolume.set_volumeType('VMFS')
        storagevolume.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )
        hostMountPoint = \
            HostMountPoint(
                {'1': '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
                 '2': 'host-9'})
        storagevolume.add_mountPoints(hostMountPoint)

        storagevolume1 = StorageVolume()
        storagevolume1.set_id('datastore-112')
        storagevolume1.set_name('datastore-112')
        storagevolume1.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2'
        )
        storagevolume1.set_size(107105746944)
        storagevolume1.set_free(32256294912)
        storagevolume1.set_vmfsVolume(False)
        storagevolume1.set_shared(False)
        storagevolume1.set_assignedServerCount(1)
        storagevolume1.set_volumeType('VMFS')
        storagevolume1.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db'
        )
        hostMountPoint1 = \
            HostMountPoint(
                {'3': '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db',
                 '4': 'host-19'})
        storagevolume1.add_mountPoints(hostMountPoint1)

        diff = ResourceModelDiff(storagevolume, storagevolume1)
        diff_res = diff.diff_resourcemodel()
        self.assertTrue(len(diff_res) > 0)
        self.assertTrue(self.update in diff_res)
        mountPoints = 'mountPoints'

        self.assertTrue(mountPoints in diff_res[self.update])
        self.assertTrue(self.update in diff_res[self.update][mountPoints])

        key = diff_res[self.update][mountPoints][self.update].keys()[0]

        self.assertTrue(self.update in diff_res[self.update][mountPoints][
            self.update][key])
        self.assertTrue('path' in diff_res[self.update][mountPoints][
            self.update][key][self.update])
        self.assertTrue(self.add in diff_res[self.update][mountPoints][
            self.update][key][self.update]['path'])
        self.assertTrue('3' in diff_res[self.update][mountPoints][
                        self.update][key][self.update]['path'][self.add])
        self.assertEquals(diff_res[self.update][mountPoints][self.update][
            key][self.update]['path'][self.add]['3'],
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db')
        self.assertTrue('4' in diff_res[self.update][mountPoints][
                        self.update][key][self.update]['path'][self.add])
        self.assertEquals(diff_res[self.update][mountPoints][self.update][
            key][self.update]['path'][self.add]['4'], 'host-19')

        self.assertTrue(self.delete in diff_res[self.update][mountPoints][
            self.update][key][self.update]['path'])
        self.assertTrue('1' in diff_res[self.update][mountPoints][
                        self.update][key][self.update]['path'][self.delete])
        self.assertEquals(diff_res[self.update][mountPoints][self.update][
            key][self.update]['path'][self.delete]['1'],
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db')
        self.assertTrue('2' in diff_res[self.update][mountPoints][
                        self.update][key][self.update]['path'][self.delete])
        self.assertEquals(diff_res[self.update][mountPoints][self.update][
            key][self.update]['path'][self.delete]['2'], 'host-9')

    '''
    This test case will check whether the old type has the unicode type
    (as when loaded from the db) and the newly created object has
    string as the attribute type.Also will check if there is the
    difference in type of old object and new object.
    '''
    def test_diff_resourcemodel_vm_with_type_changes(self):
        old_vm = Vm()
        old_vm.set_id(unicode('vm-01'))
        old_vm.set_name(unicode('vm-01'))
        disk1 = VmDisk()
        disk1.set_id(unicode('disk-01'))
        disk1.set_storageVolumeId(unicode("datastore-939"))
        old_vm.add_vmDisks(disk1)
        old_vm.set_vmHostId(unicode('host-329'))

        new_vm = Vm()
        new_vm.set_id('vm-01')
        new_vm.set_name('vm-01')
        disk3 = VmDisk()
        disk3.set_id('disk-01')
        disk3.set_storageVolumeId("datastore-939")
        new_vm.add_vmDisks(disk3)
        new_vm.set_vmHostId('host-329')

        diff = ResourceModelDiff(old_vm, new_vm)
        diff_res = diff.diff_resourcemodel()
        self.assertTrue(len(diff_res) == 0)

    def test_diff_resourcemodel_vm_with_type_changesandupdate(self):
        old_vm = Vm()
        old_vm.set_id(unicode('vm-01'))
        old_vm.set_name(unicode('vm-01'))
        disk1 = VmDisk()
        disk1.set_id(unicode('disk-01'))
        disk1.set_storageVolumeId(unicode("datastore-939"))
        old_vm.add_vmDisks(disk1)
        old_vm.set_vmHostId(unicode('host-329'))

        new_vm = Vm()
        new_vm.set_id('vm-01')
        new_vm.set_name('vm-01')
        disk3 = VmDisk()
        disk3.set_id('disk-01')
        disk3.set_storageVolumeId("datastore-939-999")
        new_vm.add_vmDisks(disk3)
        new_vm.set_vmHostId('host-329')

        diff = ResourceModelDiff(old_vm, new_vm)
        diff_res = diff.diff_resourcemodel()
        self.assertTrue(len(diff_res) > 0)
        self.assertTrue(self.update in diff_res)
        vmDisks = 'vmDisks'
        self.assertTrue(vmDisks in diff_res[self.update])

        self.assertTrue(self.update in diff_res[self.update][vmDisks])
        self.assertTrue('disk-01' in diff_res[self.update][vmDisks][
            self.update])
        self.assertTrue(self.update in diff_res[self.update][vmDisks][
            self.update]['disk-01'])
        self.assertTrue('storageVolumeId' in diff_res[self.update][vmDisks][
            self.update]['disk-01'][self.update])
        self.assertEquals(
            diff_res[self.update][vmDisks][self.update]['disk-01'][
                self.update]['storageVolumeId'], 'datastore-939-999')
