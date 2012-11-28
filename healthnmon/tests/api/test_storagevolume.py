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

from healthnmon.api import util
from healthnmon.api.storagevolume import StorageVolumeController
from healthnmon.db import api
from healthnmon.resourcemodel.healthnmonResourceModel import StorageVolume
from healthnmon.resourcemodel.healthnmonResourceModel import HostMountPoint
from nova import context
from webob.exc import HTTPNotFound
import mox
import unittest
import webob


class StorageVolumeTest(unittest.TestCase):

    """ Test cases for healthnmon resource extensions """

    expected_index_xml = \
        '<storagevolumes xmlns:atom="http://www.w3.org/2005/Atom" xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0">\
<storagevolume id="datastore-111" name="datastore-111">\
<atom:link \
href="http://localhost:8774/v2.0/storagevolumes/datastore-111" \
rel="self"/>\
<atom:link href="http://localhost:8774/storagevolumes/datastore-111" \
rel="bookmark"/>\
</storagevolume>\
<storagevolume id="datastore-112" name="datastore-112">\
<atom:link \
href="http://localhost:8774/v2.0/storagevolumes/datastore-112" \
rel="self"/>\
<atom:link href="http://localhost:8774/storagevolumes/datastore-112" \
rel="bookmark"/>\
</storagevolume>\
</storagevolumes>'
    expected_index_json = \
        '{"storagevolumes": [{"id": "datastore-111", "links": [\
{"href": "http://localhost:8774/v2.0/storagevolumes/datastore-111", \
"rel": "self"}, \
{"href": "http://localhost:8774/storagevolumes/datastore-111", \
"rel": "bookmark"}], \
"name": "datastore-111"}, \
{"id": "datastore-112", "links": [\
{"href": "http://localhost:8774/v2.0/storagevolumes/datastore-112", \
"rel": "self"}, \
{"href": "http://localhost:8774/storagevolumes/datastore-112", \
"rel": "bookmark"}], \
"name": "datastore-112"}]}'
    expected_details_json = '{"StorageVolume": {"mountPoints": {"path": "/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5da", "vmhosts": [{"id": "host-9", "links": [{"href": "http://localhost:8774/v2.0/vmhosts/host-9", "rel": "self"}, {"href": "http://localhost:8774/vmhosts/host-9", "rel": "bookmark"}]}]}, "vmfsVolume": "true", "resourceManagerId": "13274325-BFD6-464F-A9D1-61332573B5E2", "name": "datastore-111", "volumeType": "VMFS", "volumeId": "/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5da", "free": "32256294912", "assignedServerCount": "2", "shared": "true", "id": "datastore-111", "size": "107105746944"}}'
    expected_storage_details_xml = '<StorageVolume><id>datastore-111</id><name>datastore-111</name><resourceManagerId>13274325-BFD6-464F-A9D1-61332573B5E2</resourceManagerId><size>107105746944</size><free>32256294912</free><mountPoints><path>/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5da</path><vmhost xmlns:atom="http://www.w3.org/2005/Atom" id="host-9"><atom:link href="http://localhost:8774/v2.0/vmhosts/host-9" rel="self"/><atom:link href="http://localhost:8774/vmhosts/host-9" rel="bookmark"/></vmhost></mountPoints><vmfsVolume>true</vmfsVolume><shared>true</shared><assignedServerCount>2</assignedServerCount><volumeType>VMFS</volumeType><volumeId>/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5da</volumeId></StorageVolume>'
    expected_detail_xml = '<storagevolumes xmlns:atom="http://www.w3.org/2005/Atom" xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0"><StorageVolume><id>datastore-111</id><name>datastore-111</name><resourceManagerId>13274325-BFD6-464F-A9D1-61332573B5E2</resourceManagerId><size>107105746944</size><free>32256294912</free><mountPoints><path>/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5da</path><vmhost id="host-9"><atom:link href="http://localhost:8774/v2.0/vmhosts/host-9" rel="self"/><atom:link href="http://localhost:8774/vmhosts/host-9" rel="bookmark"/></vmhost></mountPoints><vmfsVolume>true</vmfsVolume><shared>true</shared><assignedServerCount>2</assignedServerCount><volumeType>VMFS</volumeType><volumeId>/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5da</volumeId></StorageVolume><StorageVolume><id>datastore-112</id><name>datastore-112</name><resourceManagerId>13274325-BFD6-464F-A9D1-61332573B5E2</resourceManagerId><size>107105746944</size><free>32256294912</free><mountPoints><path>/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db</path><vmhost id="host-9"><atom:link href="http://localhost:8774/v2.0/vmhosts/host-9" rel="self"/><atom:link href="http://localhost:8774/vmhosts/host-9" rel="bookmark"/></vmhost></mountPoints><vmfsVolume>false</vmfsVolume><shared>false</shared><assignedServerCount>1</assignedServerCount><volumeType>VMFS</volumeType><volumeId>/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db</volumeId></StorageVolume></storagevolumes>'
    expected_limited_detail_xml = '<storagevolumes xmlns:atom="http://www.w3.org/2005/Atom" xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0"><StorageVolume><id>datastore-112</id><name>datastore-112</name><resourceManagerId>13274325-BFD6-464F-A9D1-61332573B5E2</resourceManagerId><size>107105746944</size><free>32256294912</free><mountPoints><path>/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db</path><vmhost id="host-9"><atom:link href="http://localhost:8774/v2.0/vmhosts/host-9" rel="self"/><atom:link href="http://localhost:8774/vmhosts/host-9" rel="bookmark"/></vmhost></mountPoints><vmfsVolume>false</vmfsVolume><shared>false</shared><assignedServerCount>1</assignedServerCount><volumeType>VMFS</volumeType><volumeId>/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db</volumeId></StorageVolume><atom:link href="http://localhost:8774/v2.0/storagevolumes?limit=1" rel="previous"/></storagevolumes>'

    def setUp(self):
        """ Setup initial mocks and logging configuration """

        super(StorageVolumeTest, self).setUp()
        self.config_drive = None
        self.mock = mox.Mox()
        self.admin_context = context.RequestContext('admin', '',
                                                    is_admin=True)

    def tearDown(self):
        self.mock.stubs.UnsetAll()

    def test_list_storagevolumes_json(self):
        storagevolumes = self.get_storagevolume_list()
        self.mock.StubOutWithMock(api, 'storage_volume_get_all_by_filters')
        api.storage_volume_get_all_by_filters(mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg()).AndReturn(storagevolumes)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/storagevolumes.json',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = StorageVolumeController().index(request)
        self.assertNotEqual(resp, None, 'Return json string')
        self.assertEqual(self.expected_index_json, resp.body)

    def test_list_storagevolumes_xml(self):
        storagevolumes = self.get_storagevolume_list()
        self.mock.StubOutWithMock(api, 'storage_volume_get_all_by_filters')
        api.storage_volume_get_all_by_filters(mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg()).AndReturn(storagevolumes)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/storagevolumes.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = StorageVolumeController().index(request)
        self.assertNotEqual(resp, None, 'Return xml string')
        self.assertEqual(resp.body, self.expected_index_xml)

    def test_list_limited_storagevolumes_detail_xml(self):
        storagevolumes = self.get_storagevolume_list()
        self.mock.StubOutWithMock(api, 'storage_volume_get_all_by_filters')
        api.storage_volume_get_all_by_filters(mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg()).AndReturn(storagevolumes)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/storagevolumes/detail.xml?'
                                      'limit=1&marker=datastore-111',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = StorageVolumeController().detail(request)
        self.assertEqual(resp.body, self.expected_limited_detail_xml)

    def test_list_storagevolumes_detail_xml(self):
        storagevolumes = self.get_storagevolume_list()
        self.mock.StubOutWithMock(api, 'storage_volume_get_all_by_filters')
        api.storage_volume_get_all_by_filters(mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg()).AndReturn(storagevolumes)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/storagevolumes/detail.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = StorageVolumeController().detail(request)
        self.assertEqual(resp.body, self.expected_detail_xml)

    def test_list_storagevolumes_detail_none_xml(self):
        storagevolumes = None
        self.mock.StubOutWithMock(api, 'storage_volume_get_all_by_filters')
        api.storage_volume_get_all_by_filters(mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg()).AndReturn(storagevolumes)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/storagevolumes/detail.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = StorageVolumeController().detail(request)
        self.assertNotEqual(resp, None, 'Return xml string')

    def test_list_storagevolumes_xml_header(self):
        storagevolumes = self.get_storagevolume_list()
        self.mock.StubOutWithMock(api, 'storage_volume_get_all_by_filters')
        api.storage_volume_get_all_by_filters(mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg()).AndReturn(storagevolumes)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/storagevolumes',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        request.headers['Accept'] = 'application/xml'
        resp = StorageVolumeController().index(request)
        self.assertNotEqual(resp, None, 'Return xml string')
        self.assertEqual(resp.body, self.expected_index_xml)

    def test_list_storagevolumes_json_header(self):
        storagevolumes = self.get_storagevolume_list()
        self.mock.StubOutWithMock(api, 'storage_volume_get_all_by_filters')
        api.storage_volume_get_all_by_filters(mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg()).AndReturn(storagevolumes)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/storagevolumes',
                                      base_url='http://localhost:8774/v2.0/')
        request.headers['Accept'] = 'application/json'
        request.environ['nova.context'] = self.admin_context
        resp = StorageVolumeController().index(request)
        self.assertNotEqual(resp, None, 'Return json string')
        self.assertEqual(self.expected_index_json, resp.body)

    def test_storagevolume_details_json(self):
        storagevolumes = self.get_single_storagevolume()
        self.mock.StubOutWithMock(api, 'storage_volume_get_by_ids')

        api.storage_volume_get_by_ids(mox.IgnoreArg(),
                                      mox.IgnoreArg()).AndReturn(storagevolumes)
        self.mock.ReplayAll()
        request = \
            webob.Request.blank('/v2.0/storagevolumes/datastore-111.json',
                                base_url='http://localhost:8774/v2.0/'
                                )
        request.environ['nova.context'] = self.admin_context
        resp = StorageVolumeController().show(request, 'datastore-111')
        self.assertNotEqual(resp, None,
                            'Return json response for datastore-111')
        self.assertEqual(self.expected_details_json, resp.body)

    def test_storagevolume_details_xml(self):
        storagevolumes = self.get_single_storagevolume()
        self.mock.StubOutWithMock(api, 'storage_volume_get_by_ids')

        api.storage_volume_get_by_ids(mox.IgnoreArg(),
                                      mox.IgnoreArg()).AndReturn(storagevolumes)
        self.mock.ReplayAll()
        request = \
            webob.Request.blank('/v2.0/storagevolumes/datastore-111.xml',
                                base_url='http://localhost:8774/v2.0/'
                                )
        request.environ['nova.context'] = self.admin_context
        resp = StorageVolumeController().show(request, 'datastore-111')
        self.assertNotEqual(resp, None,
                            'Return xml response for datastore-111')
        self.assertEqual(self.expected_storage_details_xml, resp.body)

    def test_storagevolume_details_none_xml(self):
        storagevolumes = None
        self.mock.StubOutWithMock(api, 'storage_volume_get_by_ids')

        api.storage_volume_get_by_ids(mox.IgnoreArg(),
                                      mox.IgnoreArg()).AndReturn(storagevolumes)
        self.mock.ReplayAll()
        request = \
            webob.Request.blank('/v2.0/storagevolumes/datastore-111.xml',
                                base_url='http://localhost:8774/v2.0/'
                                )
        request.environ['nova.context'] = self.admin_context
        resp = StorageVolumeController().show(request, 'datastore-111')
        self.assertNotEqual(resp, None,
                            'Return xml response for datastore-111')

    def test_storagevolume_details_json_exception(self):
        storagevolumes = self.get_storagevolume_list()
        xml_utils = util
        self.mock.StubOutWithMock(xml_utils, 'xml_to_dict')
        xml_utils.xml_to_dict(mox.IgnoreArg()).AndRaise(Exception(
            'Test Exception'))
        self.mock.StubOutWithMock(api, 'storage_volume_get_by_ids')

        api.storage_volume_get_by_ids(mox.IgnoreArg(),
                                      mox.IgnoreArg()).AndReturn(storagevolumes)
        self.mock.ReplayAll()
        request = \
            webob.Request.blank('/v2.0/storagevolumes/datastore-111.json',
                                base_url='http://localhost:8774/v2.0/'
                                )
        request.environ['nova.context'] = self.admin_context
        resp = StorageVolumeController().show(request, 'datastore-111')
        self.assertTrue(isinstance(resp, HTTPNotFound))

    def test_list_storagevolumes_none_check(self):
        self.mock.StubOutWithMock(api, 'storage_volume_get_all_by_filters')
        api.storage_volume_get_all_by_filters(mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg()).AndReturn(None)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/storagevolumes',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = StorageVolumeController().index(request)
        self.assertEqual(resp.body, '{"storagevolumes": []}',
                         'Return xml string')

    def test_query_field_key(self):
        storagevolumes = self.get_single_storagevolume()
        self.mock.StubOutWithMock(api, 'storage_volume_get_by_ids')

        api.storage_volume_get_by_ids(mox.IgnoreArg(),
                                      mox.IgnoreArg()).AndReturn(storagevolumes)
        self.mock.ReplayAll()
        request = \
            webob.Request.blank(
                '/v2.0/storagevolumes/datastore-111.json?fields=id,name',
                base_url='http://localhost:8774/v2.0/'
            )
        request.environ['nova.context'] = self.admin_context
        resp = StorageVolumeController().show(request, 'datastore-111')
        self.assertNotEqual(resp, None,
                            'Return xml response for datastore-111')
        self.mock.stubs.UnsetAll()

    def get_single_storagevolume(self, storageId=None):

        # storagevolume_list = []

        if storageId is not None:
            self.get_storagevolume_list(storageId)
        return self.get_storagevolume_list()

    def get_storagevolume_list(self, storageId=None):
        storagevolume_dict = {}
        storagevolume_list = []
        storagevolume = StorageVolume()
        storagevolume.set_id('datastore-111')
        storagevolume.set_name('datastore-111')
        storagevolume.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2')
        storagevolume.set_size(107105746944)
        storagevolume.set_free(32256294912)
        storagevolume.set_vmfsVolume(True)
        storagevolume.set_shared(True)
        storagevolume.set_assignedServerCount(2)
        storagevolume.set_volumeType('VMFS')
        storagevolume.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5da')
        hostMountPoint = \
            HostMountPoint(
                '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5da', 'host-9')
        storagevolume.add_mountPoints(hostMountPoint)
        storagevolume_list.append(storagevolume)
        storagevolume_dict[storagevolume.get_id()] = storagevolume

        storagevolume = StorageVolume()
        storagevolume.set_id('datastore-112')
        storagevolume.set_name('datastore-112')
        storagevolume.set_resourceManagerId(
            '13274325-BFD6-464F-A9D1-61332573B5E2')
        storagevolume.set_size(107105746944)
        storagevolume.set_free(32256294912)
        storagevolume.set_vmfsVolume(False)
        storagevolume.set_shared(False)
        storagevolume.set_assignedServerCount(1)
        storagevolume.set_volumeType('VMFS')
        storagevolume.set_volumeId(
            '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db')
        hostMountPoint = \
            HostMountPoint(
                '/vmfs/volumes/4e374cf3-328f8064-aa2c-78acc0fcb5db', 'host-9')
        storagevolume.add_mountPoints(hostMountPoint)
        storagevolume_list.append(storagevolume)
        storagevolume_dict[storagevolume.get_id()] = storagevolume
        if storageId is not None:
            return [storagevolume_dict[storageId]]
        return storagevolume_list


if __name__ == '__main__':
    unittest.main()
