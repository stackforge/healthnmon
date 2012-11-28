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
import webob
import mox
import json
from webob.exc import HTTPNotFound

from nova.openstack.common import rpc
from nova import context
from healthnmon.db import api
from healthnmon.api import util
from healthnmon.resourcemodel.healthnmonResourceModel import Vm
from healthnmon.resourcemodel.healthnmonResourceModel import VmDisk
from healthnmon.api.vm import VMController

from lxml import etree
from lxml import objectify
from StringIO import StringIO


class VMTest(unittest.TestCase):

    """ Tests for VM extension """
    expected_identifier_show_json = '{"Vm": {"id": "vm-01", "name": "vm-01"}}'
    expected_identifier_detail_json = '{"virtualmachines": [{"id": "vm-01", "name": "vm-01"}, {"id": "vm-02", "name": "vm-02"}]}'
    expected_identifier_show_xml = '<Vm><id>vm-01</id><vmDisks><storagevolume xmlns:atom="http://www.w3.org/2005/Atom" id="datastore-999"><atom:link href="http://localhost:8774/v2.0/storagevolumes/datastore-999" rel="self"/><atom:link href="http://localhost:8774/storagevolumes/datastore-999" rel="bookmark"/></storagevolume></vmDisks></Vm>'
    expected_identifier_detail_xml = '<virtualmachines xmlns:atom="http://www.w3.org/2005/Atom" xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0"><Vm><id>vm-01</id><vmDisks><storagevolume id="datastore-999"><atom:link href="http://localhost:8774/v2.0/storagevolumes/datastore-999" rel="self"/><atom:link href="http://localhost:8774/storagevolumes/datastore-999" rel="bookmark"/></storagevolume></vmDisks></Vm><Vm/></virtualmachines>'

    def setUp(self):
        """ Setup initial mocks and logging configuration """

        super(VMTest, self).setUp()
        self.config_drive = None
        self.mock = mox.Mox()
        self.admin_context = context.RequestContext('admin', '',
                                                    is_admin=True)

    def tearDown(self):
        self.mock.stubs.UnsetAll()

    def test_list_vm_json(self):
        expected_out_json = \
            '{"virtualmachines": [{"id": "vm-01", "links": [{"href": "http://localhost:8774/v2.0/virtualmachines/vm-01", "rel": "self"}, \
        {"href": "http://localhost:8774/virtualmachines/vm-01", "rel": "bookmark"}], "name": "vm-01"}, {"id": "vm-02", "links": \
        [{"href": "http://localhost:8774/v2.0/virtualmachines/vm-02", "rel": "self"}, \
        {"href": "http://localhost:8774/virtualmachines/vm-02", "rel": "bookmark"}], "name": "vm-02"}]}'

        vm_list = self.get_vm_list()
        self.mock.StubOutWithMock(api, 'vm_get_all_by_filters')
        api.vm_get_all_by_filters(mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg()).AndReturn(vm_list)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/virtualmachines.json',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VMController().index(request)
        self.assertNotEqual(resp, None, 'Return json string')
        self.compare_json(expected_out_json, resp.body)

#        self.assertEqual(self.expected_index_json, resp.body)

        self.mock.stubs.UnsetAll()

    def test_list_vm_detail_xml(self):
        vms = self.get_vm_list()
        self.mock.StubOutWithMock(api, 'vm_get_all_by_filters')
        api.vm_get_all_by_filters(mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg()).AndReturn(vms)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/virtualmachines/detail.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VMController().detail(request)
        self.assertNotEqual(resp, None, 'Return xml string')
        self.mock.stubs.UnsetAll()

    def test_vm_none_detail_xml(self):
        vms = None
        self.mock.StubOutWithMock(api, 'vm_get_all_by_filters')
        api.vm_get_all_by_filters(mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg()).AndReturn(vms)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/virtualmachines/detail.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VMController().detail(request)
        self.assertNotEqual(resp, None, 'Return xml string')
        self.mock.stubs.UnsetAll()

    def test_list_vm_detail_json(self):
        vms = self.get_vm_list()
        self.mock.StubOutWithMock(api, 'vm_get_all_by_filters')
        api.vm_get_all_by_filters(mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg()).AndReturn(vms)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/virtualmachines/detail',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VMController().detail(request)
        self.assertNotEqual(resp, None, 'Return json string')
        self.mock.stubs.UnsetAll()

    def test_list_vm_xml(self):
        expected_out_xml = \
            '<virtualmachines xmlns:atom="http://www.w3.org/2005/Atom" xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0">\
        <vm id="vm-01" name="vm-01"><atom:link href="http://localhost:8774/v2.0/virtualmachines/vm-01" rel="self"/>\
        <atom:link href="http://localhost:8774/virtualmachines/vm-01" rel="bookmark"/></vm>\
        <vm id="vm-02" name="vm-02"><atom:link href="http://localhost:8774/v2.0/virtualmachines/vm-02" rel="self"/>\
        <atom:link href="http://localhost:8774/virtualmachines/vm-02" rel="bookmark"/></vm>\
        </virtualmachines>'

        vm_list = self.get_vm_list()
        self.mock.StubOutWithMock(api, 'vm_get_all_by_filters')
        api.vm_get_all_by_filters(mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg()).AndReturn(vm_list)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vm.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VMController().index(request)
        self.assertNotEqual(resp, None, 'Return xml string')
        self.compare_xml(expected_out_xml, resp.body)

#        self.assertEqual(resp.body, self.expected_index_xml)

        self.mock.stubs.UnsetAll()

    def test_vm_details_none_xml(self):
        vm_list = None
        self.mock.StubOutWithMock(api, 'vm_get_by_ids')
        api.vm_get_by_ids(mox.IgnoreArg(),
                          mox.IgnoreArg()).AndReturn(vm_list)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vm/vm-01.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VMController().show(request, 'vm-01')
        self.assertNotEqual(resp, None, 'Return xml response for vm-01')
        self.mock.stubs.UnsetAll()

    def test_list_vm_xml_header(self):
        expected_out_xml = \
            '<virtualmachines xmlns:atom="http://www.w3.org/2005/Atom" xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0">\
        <vm id="vm-01" name="vm-01"><atom:link href="http://localhost:8774/v2.0/virtualmachines/vm-01" rel="self"/>\
        <atom:link href="http://localhost:8774/virtualmachines/vm-01" rel="bookmark"/></vm>\
        <vm id="vm-02" name="vm-02"><atom:link href="http://localhost:8774/v2.0/virtualmachines/vm-02" rel="self"/>\
        <atom:link href="http://localhost:8774/virtualmachines/vm-02" rel="bookmark"/></vm>\
        </virtualmachines>'

        virtualmachines = self.get_vm_list()
        self.mock.StubOutWithMock(api, 'vm_get_all_by_filters')
        api.vm_get_all_by_filters(mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg()).AndReturn(virtualmachines)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vm',
                                      base_url='http://localhost:8774/v2.0/')
        request.headers['Accept'] = 'application/xml'
        request.environ['nova.context'] = self.admin_context
        resp = VMController().index(request)
        self.assertNotEqual(resp, None, 'Return xml string')
        self.compare_xml(expected_out_xml, resp.body)
#        self.assertEqual(resp.body, self.expected_index_xml)

        self.mock.stubs.UnsetAll()

    def test_list_vm_json_header(self):
        expected_out_json = \
            '{"virtualmachines": [{"id": "vm-01", "links": [{"href": "http://localhost:8774/v2.0/virtualmachines/vm-01", "rel": "self"}, \
        {"href": "http://localhost:8774/virtualmachines/vm-01", "rel": "bookmark"}], "name": "vm-01"}, \
        {"id": "vm-02", "links": [{"href": "http://localhost:8774/v2.0/virtualmachines/vm-02", "rel": "self"}, \
        {"href": "http://localhost:8774/virtualmachines/vm-02", "rel": "bookmark"}], "name": "vm-02"}]}'

        virtualmachines = self.get_vm_list()
        self.mock.StubOutWithMock(api, 'vm_get_all_by_filters')
        api.vm_get_all_by_filters(mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg()).AndReturn(virtualmachines)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vm',
                                      base_url='http://localhost:8774/v2.0/')
        request.headers['Accept'] = 'application/json'
        request.environ['nova.context'] = self.admin_context
        resp = VMController().index(request)
        self.assertNotEqual(resp, None, 'Return json string')
        self.compare_json(expected_out_json, resp.body)

#        self.assertEqual(self.expected_index_json, resp.body)

        self.mock.stubs.UnsetAll()

    def test_list_virtual_machine_none_check(self):
        self.mock.StubOutWithMock(api, 'vm_get_all_by_filters')
        api.vm_get_all_by_filters(mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg(),
                                  mox.IgnoreArg()).AndReturn(None)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/virtualmachines',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VMController().index(request)
        self.assertEqual(resp.body, '{"virtualmachines": []}',
                         'Return json string')

    def test_vm_details_json(self):
        expected_out_json = \
            '{"Vm": {"vmDisks": [{"storagevolumes": [{"id": "datastore-939", \
        "links": [{"href": "http://localhost:8774/v2.0/storagevolumes/datastore-939", "rel": "self"}, \
        {"href": "http://localhost:8774/storagevolumes/datastore-939", "rel": "bookmark"}]}], "id": "disk-01"}, \
        {"storagevolumes": [{"id": "datastore-439", "links": [{"href": "http://localhost:8774/v2.0/storagevolumes/datastore-439", "rel": "self"}, \
        {"href": "http://localhost:8774/storagevolumes/datastore-439", "rel": "bookmark"}]}], "id": "disk-02"}], \
        "vmhosts": [{"id": "host-329", "links": [{"href": "http://localhost:8774/v2.0/vmhosts/host-329", "rel": "self"}, \
        {"href": "http://localhost:8774/vmhosts/host-329", "rel": "bookmark"}]}], "id": "vm-01", "name": "vm-01"}}'

        vm_list = self.get_single_vm()
        self.mock.StubOutWithMock(api, 'vm_get_by_ids')

        api.vm_get_by_ids(mox.IgnoreArg(),
                          mox.IgnoreArg()).AndReturn(vm_list)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vm/vm-01.json',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VMController().show(request, 'vm-01')
        self.assertNotEqual(resp, None, 'Return json response for vm-01'
                            )
        self.compare_json(expected_out_json, resp.body)
        self.mock.stubs.UnsetAll()

    def test_vm_details_xml(self):
        expected_out_xml = \
            '<Vm><id>vm-01</id><name>vm-01</name>\
        <vmDisks><id>disk-01</id><storagevolume xmlns:atom="http://www.w3.org/2005/Atom" id="datastore-939">\
        <atom:link href="http://localhost:8774/v2.0/storagevolumes/datastore-939" rel="self"/>\
        <atom:link href="http://localhost:8774/storagevolumes/datastore-939" rel="bookmark"/>\
        </storagevolume></vmDisks><vmDisks><id>disk-02</id>\
        <storagevolume xmlns:atom="http://www.w3.org/2005/Atom" id="datastore-439">\
        <atom:link href="http://localhost:8774/v2.0/storagevolumes/datastore-439" rel="self"/>\
        <atom:link href="http://localhost:8774/storagevolumes/datastore-439" rel="bookmark"/></storagevolume></vmDisks>\
        <vmhost xmlns:atom="http://www.w3.org/2005/Atom" id="host-329"><atom:link href="http://localhost:8774/v2.0/vmhosts/host-329" rel="self"/>\
        <atom:link href="http://localhost:8774/vmhosts/host-329" rel="bookmark"/></vmhost></Vm>'

        vm_list = self.get_single_vm()
        self.mock.StubOutWithMock(api, 'vm_get_by_ids')

        api.vm_get_by_ids(mox.IgnoreArg(),
                          mox.IgnoreArg()).AndReturn(vm_list)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vm/vm-01.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VMController().show(request, 'vm-01')
        self.assertNotEqual(resp, None, 'Return xml response for vm-01')
        self.compare_xml(expected_out_xml, resp.body)
        self.mock.stubs.UnsetAll()

    def test_vm_details_json_exception(self):
        vm_list = self.get_single_vm()
        xml_utils = util
        self.mock.StubOutWithMock(xml_utils, 'xml_to_dict')
        xml_utils.xml_to_dict(mox.IgnoreArg()).AndRaise(IndexError('Test index'
                                                                   ))
        self.mock.StubOutWithMock(api, 'vm_get_by_ids')

        api.vm_get_by_ids(mox.IgnoreArg(),
                          mox.IgnoreArg()).AndReturn(vm_list)
        self.mock.ReplayAll()
        request = webob.Request.blank(
            '/v2.0/virtualmachines/vm-01.json',
            base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VMController().show(request, 'vm-01')
        self.assertTrue(isinstance(resp, HTTPNotFound))

    def test_query_field_key(self):
        expected_out_json = \
            '{"Vm": {"id": "vm-01", "name": "vm-01"}}'

        vm_list = self.get_single_vm()
        self.mock.StubOutWithMock(api, 'vm_get_by_ids')

        api.vm_get_by_ids(mox.IgnoreArg(),
                          mox.IgnoreArg()).AndReturn(vm_list)
        self.mock.StubOutWithMock(rpc, 'call')

        rpc.call(mox.IgnoreArg(), mox.IgnoreArg(),
                 mox.IgnoreArg()).AndReturn(self.get_resource_utilization())
        self.mock.ReplayAll()
        request = \
            webob.Request.blank('/v2.0/vm/vm-01.json?fields=id,name',
                                base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VMController().show(request, 'vm-01')
        self.assertNotEqual(resp, None, 'Return xml response for vm-01')
        self.compare_json(expected_out_json, resp.body)
        self.mock.stubs.UnsetAll()

    def test_utilization(self):
        vm_list = self.get_single_vm()
        self.mock.StubOutWithMock(api, 'vm_get_by_ids')

        api.vm_get_by_ids(mox.IgnoreArg(),
                          mox.IgnoreArg()).AndReturn(vm_list)
        self.mock.StubOutWithMock(rpc, 'call')

        rpc.call(mox.IgnoreArg(), mox.IgnoreArg(),
                 mox.IgnoreArg()).AndReturn(self.get_resource_utilization())
        self.mock.ReplayAll()
        request = \
            webob.Request.blank(
                '/v2.0/vm/vm-01.xml?fields=utilization',
                base_url='http://localhost:8774/v2.0/'
            )
        request.environ['nova.context'] = self.admin_context
        resp = VMController().show(request, 'vm-01')
        self.assertNotEqual(resp, None, 'Return xml response for vm-01')

    def test_utilization_query(self):
        vm_list = self.get_single_vm()
        self.mock.StubOutWithMock(api, 'vm_get_by_ids')

        api.vm_get_by_ids(mox.IgnoreArg(),
                          mox.IgnoreArg()).AndReturn(vm_list)
        self.mock.StubOutWithMock(rpc, 'call')

        rpc.call(mox.IgnoreArg(), mox.IgnoreArg(),
                 mox.IgnoreArg()).AndReturn(self.get_resource_utilization())
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vm/vm-01.xml?utilization',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VMController().show(request, 'vm-01')
        self.assertNotEqual(resp, None, 'Return xml response for vm-01')

    def test_vm_identifier_json(self):
        request = webob.Request.blank(
            '/v2.0/virtualmachines/vm-01?fields=name',
            base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        item_list = self.get_vm_list()
        self.assertEquals(VMController()._show(request, item_list[0]).body,
                          self.expected_identifier_show_json)
        self.assertEquals(VMController()._detail(request, item_list, []).body,
                          self.expected_identifier_detail_json)

    def test_vm_identifier_xml(self):
        request = webob.Request.blank(
            '/v2.0/virtualmachines/vm-01.xml?fields=vmDisks',
            base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        item_list = self.get_vm_list()
        self.assertEquals(VMController()._show(request, item_list[0]).body,
                          self.expected_identifier_show_xml)
        self.assertEquals(VMController()._detail(request, item_list, []).body,
                          self.expected_identifier_detail_xml)

    def get_single_vm(self):
        vm_list = []
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
        vm_list.append(vm)
        return vm_list

    def get_vm_list(self):
        vm_list = []
        vm = Vm()
        vm.set_id('vm-01')
        vm.set_name('vm-01')
        disk = VmDisk()
        disk.set_storageVolumeId('datastore-999')
        vm.set_vmHostId('host-1234')
        vm.add_vmDisks(disk)
        vm_list.append(vm)
        vm = Vm()
        vm.set_id('vm-02')
        vm.set_name('vm-02')
        vm_list.append(vm)
        return vm_list

    def get_resource_utilization(self):
        resource_dict = {
            'resourceId': '23224u230',
            'granularity': 2,
            'cpuUserLoad': 4.2,
            'cpuSystemLoad': 5.2,
            'hostCpuSpeed': 2323312,
            'hostMaxCpuSpeed': 92898392838,
            'ncpus': 8,
            'diskRead': 89.2,
            'diskWrite': 23.1,
            'netRead': 80,
            'netWrite': 20,
            'totalMemory': 4096 * 6,
            'freeMemory': 4096 * 2,
            'uptimeMinute': 4820934802,
            'reservedSystemCapacity': 7423849234,
            'maximumSystemCapacity': 23479237492839,
            'relativeWeight': 293472938,
            'reservedSystemMemory': 38929823983,
            'maximumSystemMemory': 2398293832,
            'memoryRelativeWeight': 89239823,
        }
        return dict(ResourceUtilization=resource_dict)

    def compare_xml(self, expected, actual):
        expectedObject = objectify.fromstring(expected)
        expected = etree.tostring(expectedObject)
        actualObject = objectify.fromstring(actual)
        actual = etree.tostring(actualObject)
        self.assertEquals(expected, actual)

    def compare_json(self, expected, actual):
        expectedObject = json.load(StringIO(expected))
        actualObject = json.load(StringIO(actual))
        self.assertEquals(expectedObject, actualObject)

if __name__ == '__main__':

    # import sys;sys.argv = ['', 'Test.testName']

    unittest.main()
