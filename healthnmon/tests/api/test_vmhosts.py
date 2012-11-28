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
from healthnmon.api.vmhosts import VmHostsController
from healthnmon.db import api
from healthnmon.resourcemodel.healthnmonResourceModel import VmHost
from nova.openstack.common import rpc
from nova import context
from webob.exc import HTTPNotFound
import mox
import unittest
import webob


class VmHostsTest(unittest.TestCase):

    """ Test cases for healthnmon resource extensions """

    expected_index_xml = \
        '<vmhosts xmlns:atom="http://www.w3.org/2005/Atom" \
xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0">\
<vmhost id="host-01" name="host-01">\
<atom:link \
href="http://localhost:8774/v2.0/vmhosts/host-01" rel="self"/>\
<atom:link href="http://localhost:8774/vmhosts/host-01" rel="bookmark"/>\
</vmhost>\
<vmhost id="host-02" name="host-02">\
<atom:link href="http://localhost:8774/v2.0/vmhosts/host-02" rel="self"/>\
<atom:link href="http://localhost:8774/vmhosts/host-02" rel="bookmark"/>\
</vmhost></vmhosts>'
    expected_index_json = \
        '{"vmhosts": [{"id": "host-01", "links": \
[{"href": "http://localhost:8774/v2.0/vmhosts/host-01", "rel": "self"}, \
{"href": "http://localhost:8774/vmhosts/host-01", "rel": "bookmark"}], \
"name": "host-01"}, {"id": "host-02", "links": \
[{"href": "http://localhost:8774/v2.0/vmhosts/host-02", "rel": "self"}, \
{"href": "http://localhost:8774/vmhosts/host-02", "rel": "bookmark"}], \
"name": "host-02"}]}'
    expected_index_limited_json = '{"vmhosts": [{"id": "host-2", "links": [{"href": "http://localhost:8774/v2.0/vmhosts/host-2", "rel": "self"}, {"href": "http://localhost:8774/vmhosts/host-2", "rel": "bookmark"}], "name": "host-2"}], "vmhosts_links": [{"href": "http://localhost:8774/v2.0/vmhosts?limit=1&marker=host-2", "rel": "next"}, {"href": "http://localhost:8774/v2.0/vmhosts?limit=1", "rel": "previous"}]}'
    expected_index_limited_previous_json = '{"vmhosts": [{"id": "host-3", "links": [{"href": "http://localhost:8774/v2.0/vmhosts/host-3", "rel": "self"}, {"href": "http://localhost:8774/vmhosts/host-3", "rel": "bookmark"}], "name": "host-3"}], "vmhosts_links": [{"href": "http://localhost:8774/v2.0/vmhosts?limit=1&marker=host-1", "rel": "previous"}]}'
    expected_index_limited_xml = '<vmhosts xmlns:atom="http://www.w3.org/2005/Atom" xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0"><vmhost id="host-2" name="host-2"><atom:link href="http://localhost:8774/v2.0/vmhosts/host-2" rel="self"/><atom:link href="http://localhost:8774/vmhosts/host-2" rel="bookmark"/></vmhost><atom:link href="http://localhost:8774/v2.0/vmhosts?limit=1&amp;marker=host-2" rel="next"/><atom:link href="http://localhost:8774/v2.0/vmhosts?limit=1" rel="previous"/></vmhosts>'
    expected_detail_xml = \
        '<vmhosts xmlns:atom="http://www.w3.org/2005/Atom" \
xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0">\
<VmHost><id>host-01</id><name>host-01</name><storagevolume id="storage-01">\
<atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-01" \
rel="self"/><atom:link href="http://localhost:8774/storagevolumes/storage-01" \
rel="bookmark"/></storagevolume><storagevolume id="storage-02">\
<atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-02" \
rel="self"/><atom:link href="http://localhost:8774/storagevolumes/storage-02" \
rel="bookmark"/></storagevolume><virtualmachine id="vm-01">\
<atom:link href="http://localhost:8774/v2.0/virtualmachines/vm-01" \
rel="self"/><atom:link href="http://localhost:8774/virtualmachines/vm-01" \
rel="bookmark"/></virtualmachine>\
<virtualmachine id="vm-02">\
<atom:link href="http://localhost:8774/v2.0/virtualmachines/vm-02" \
rel="self"/>\
<atom:link href="http://localhost:8774/virtualmachines/vm-02" rel="bookmark"/>\
</virtualmachine></VmHost><VmHost><id>host-02</id><name>host-02</name>\
<storagevolume id="storage-03">\
<atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-03" \
rel="self"/>\
<atom:link href="http://localhost:8774/storagevolumes/storage-03" \
rel="bookmark"/></storagevolume>\
<storagevolume id="storage-04">\
<atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-04" \
rel="self"/>\
<atom:link href="http://localhost:8774/storagevolumes/storage-04" \
rel="bookmark"/></storagevolume><virtualmachine id="vm-03">\
<atom:link href="http://localhost:8774/v2.0/virtualmachines/vm-03" \
rel="self"/><atom:link href="http://localhost:8774/virtualmachines/vm-03" \
rel="bookmark"/></virtualmachine><virtualmachine id="vm-04">\
<atom:link href="http://localhost:8774/v2.0/virtualmachines/vm-04" \
rel="self"/><atom:link href="http://localhost:8774/virtualmachines/vm-04" \
rel="bookmark"/></virtualmachine></VmHost></vmhosts>'
    expected_detail_json = '{"vmhosts": [{"virtualmachines": [{"id": "vm-01", "links": [{"href": "http://localhost:8774/v2.0/virtualmachines/vm-01", "rel": "self"}, {"href": "http://localhost:8774/virtualmachines/vm-01", "rel": "bookmark"}]}, {"id": "vm-02", "links": [{"href": "http://localhost:8774/v2.0/virtualmachines/vm-02", "rel": "self"}, {"href": "http://localhost:8774/virtualmachines/vm-02", "rel": "bookmark"}]}], "id": "host-01", "storagevolumes": [{"id": "storage-01", "links": [{"href": "http://localhost:8774/v2.0/storagevolumes/storage-01", "rel": "self"}, {"href": "http://localhost:8774/storagevolumes/storage-01", "rel": "bookmark"}]}, {"id": "storage-02", "links": [{"href": "http://localhost:8774/v2.0/storagevolumes/storage-02", "rel": "self"}, {"href": "http://localhost:8774/storagevolumes/storage-02", "rel": "bookmark"}]}], "name": "host-01"}, {"virtualmachines": [{"id": "vm-03", "links": [{"href": "http://localhost:8774/v2.0/virtualmachines/vm-03", "rel": "self"}, {"href": "http://localhost:8774/virtualmachines/vm-03", "rel": "bookmark"}]}, {"id": "vm-04", "links": [{"href": "http://localhost:8774/v2.0/virtualmachines/vm-04", "rel": "self"}, {"href": "http://localhost:8774/virtualmachines/vm-04", "rel": "bookmark"}]}], "id": "host-02", "storagevolumes": [{"id": "storage-03", "links": [{"href": "http://localhost:8774/v2.0/storagevolumes/storage-03", "rel": "self"}, {"href": "http://localhost:8774/storagevolumes/storage-03", "rel": "bookmark"}]}, {"id": "storage-04", "links": [{"href": "http://localhost:8774/v2.0/storagevolumes/storage-04", "rel": "self"}, {"href": "http://localhost:8774/storagevolumes/storage-04", "rel": "bookmark"}]}], "name": "host-02"}]}'
    expected_detall_limited_previous_xml = '<vmhosts xmlns:atom="http://www.w3.org/2005/Atom" xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0"><VmHost><id>host-02</id><name>host-02</name><storagevolume id="storage-03"><atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-03" rel="self"/><atom:link href="http://localhost:8774/storagevolumes/storage-03" rel="bookmark"/></storagevolume><storagevolume id="storage-04"><atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-04" rel="self"/><atom:link href="http://localhost:8774/storagevolumes/storage-04" rel="bookmark"/></storagevolume><virtualmachine id="vm-03"><atom:link href="http://localhost:8774/v2.0/virtualmachines/vm-03" rel="self"/><atom:link href="http://localhost:8774/virtualmachines/vm-03" rel="bookmark"/></virtualmachine><virtualmachine id="vm-04"><atom:link href="http://localhost:8774/v2.0/virtualmachines/vm-04" rel="self"/><atom:link href="http://localhost:8774/virtualmachines/vm-04" rel="bookmark"/></virtualmachine></VmHost><atom:link href="http://localhost:8774/v2.0/vmhosts?limit=1" rel="previous"/></vmhosts>'
    expected_detall_limited_xml = \
        '<vmhosts xmlns:atom="http://www.w3.org/2005/Atom" \
xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0">\
<VmHost><id>host-02</id><name>host-02</name><storagevolume id="storage-03">\
<atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-03" \
rel="self"/><atom:link href="http://localhost:8774/storagevolumes/storage-03" \
rel="bookmark"/></storagevolume><storagevolume id="storage-04">\
<atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-04" \
rel="self"/><atom:link href="http://localhost:8774/storagevolumes/storage-04" \
rel="bookmark"/></storagevolume><virtualmachine id="vm-03">\
<atom:link href="http://localhost:8774/v2.0/virtualmachines/vm-03" \
rel="self"/><atom:link href="http://localhost:8774/virtualmachines/vm-03" \
rel="bookmark"/></virtualmachine><virtualmachine id="vm-04">\
<atom:link href="http://localhost:8774/v2.0/virtualmachines/vm-04" \
rel="self"/><atom:link href="http://localhost:8774/virtualmachines/vm-04" \
rel="bookmark"/></virtualmachine></VmHost>\
<atom:link \
href="http://localhost:8774/v2.0/vmhosts?limit=1&amp;marker=host-02" \
rel="next"/></vmhosts>'
    expected_limited_detail_json = '{"VmHost": {"virtualmachines": [{"id": "vm-01", "links": [{"href": "http://localhost:8774/v2.0/virtualmachines/vm-01", "rel": "self"}, {"href": "http://localhost:8774/virtualmachines/vm-01", "rel": "bookmark"}]}, {"id": "vm-02", "links": [{"href": "http://localhost:8774/v2.0/virtualmachines/vm-02", "rel": "self"}, {"href": "http://localhost:8774/virtualmachines/vm-02", "rel": "bookmark"}]}], "id": "host-01", "storagevolumes": [{"id": "storage-01", "links": [{"href": "http://localhost:8774/v2.0/storagevolumes/storage-01", "rel": "self"}, {"href": "http://localhost:8774/storagevolumes/storage-01", "rel": "bookmark"}]}, {"id": "storage-02", "links": [{"href": "http://localhost:8774/v2.0/storagevolumes/storage-02", "rel": "self"}, {"href": "http://localhost:8774/storagevolumes/storage-02", "rel": "bookmark"}]}], "name": "host-01"}}'
    expected_detail_limit_marker_json = '{"vmhosts": [{"virtualmachines": [{"id": "vm-03", "links": [{"href": "http://localhost:8774/v2.0/virtualmachines/vm-03", "rel": "self"}, {"href": "http://localhost:8774/virtualmachines/vm-03", "rel": "bookmark"}]}, {"id": "vm-04", "links": [{"href": "http://localhost:8774/v2.0/virtualmachines/vm-04", "rel": "self"}, {"href": "http://localhost:8774/virtualmachines/vm-04", "rel": "bookmark"}]}], "id": "host-02", "storagevolumes": [{"id": "storage-03", "links": [{"href": "http://localhost:8774/v2.0/storagevolumes/storage-03", "rel": "self"}, {"href": "http://localhost:8774/storagevolumes/storage-03", "rel": "bookmark"}]}, {"id": "storage-04", "links": [{"href": "http://localhost:8774/v2.0/storagevolumes/storage-04", "rel": "self"}, {"href": "http://localhost:8774/storagevolumes/storage-04", "rel": "bookmark"}]}], "name": "host-02"}], "vmhosts_links": [{"href": "http://localhost:8774/v2.0/vmhosts?limit=1", "rel": "previous"}]}'
    expected_detail_limit_marker_xml = '<VmHost><id>host-01</id><name>host-01</name><storagevolume xmlns:atom="http://www.w3.org/2005/Atom" id="storage-01"><atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-01" rel="self"/><atom:link href="http://localhost:8774/storagevolumes/storage-01" rel="bookmark"/></storagevolume><storagevolume xmlns:atom="http://www.w3.org/2005/Atom" id="storage-02"><atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-02" rel="self"/><atom:link href="http://localhost:8774/storagevolumes/storage-02" rel="bookmark"/></storagevolume><virtualmachine xmlns:atom="http://www.w3.org/2005/Atom" id="vm-01"><atom:link href="http://localhost:8774/v2.0/virtualmachines/vm-01" rel="self"/><atom:link href="http://localhost:8774/virtualmachines/vm-01" rel="bookmark"/></virtualmachine><virtualmachine xmlns:atom="http://www.w3.org/2005/Atom" id="vm-02"><atom:link href="http://localhost:8774/v2.0/virtualmachines/vm-02" rel="self"/><atom:link href="http://localhost:8774/virtualmachines/vm-02" rel="bookmark"/></virtualmachine></VmHost>'
    expected_query_id_name = '{"VmHost": {"id": "host-01", "name": "host-01"}}'
    expected_utilization_json = '{"VmHost": {"id": "host-01", "utilization": {"cpuUserLoad": "4.200000e+00", "netRead": "8.000000e+01", "maximumSystemMemory": "2398293832", "hostMaxCpuSpeed": "92898392838", "reservedSystemMemory": "38929823983", "diskRead": "8.920000e+01", "resourceId": "23224u230", "ncpus": "8", "granularity": "2", "totalMemory": "24576", "netWrite": "2.000000e+01", "freeMemory": "8192", "memoryRelativeWeight": "89239823", "diskWrite": "2.310000e+01", "relativeWeight": "293472938", "hostCpuSpeed": "2323312", "uptimeMinute": "4820934802", "maximumSystemCapacity": "23479237492839", "cpuSystemLoad": "5.200000e+00", "reservedSystemCapacity": "7423849234"}}}'
    expected_utilization_xml = '<VmHost><id>host-01</id><name>host-01</name><storagevolume xmlns:atom="http://www.w3.org/2005/Atom" id="storage-01"><atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-01" rel="self"/><atom:link href="http://localhost:8774/storagevolumes/storage-01" rel="bookmark"/></storagevolume><storagevolume xmlns:atom="http://www.w3.org/2005/Atom" id="storage-02"><atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-02" rel="self"/><atom:link href="http://localhost:8774/storagevolumes/storage-02" rel="bookmark"/></storagevolume><virtualmachine xmlns:atom="http://www.w3.org/2005/Atom" id="vm-01"><atom:link href="http://localhost:8774/v2.0/virtualmachines/vm-01" rel="self"/><atom:link href="http://localhost:8774/virtualmachines/vm-01" rel="bookmark"/></virtualmachine><virtualmachine xmlns:atom="http://www.w3.org/2005/Atom" id="vm-02"><atom:link href="http://localhost:8774/v2.0/virtualmachines/vm-02" rel="self"/><atom:link href="http://localhost:8774/virtualmachines/vm-02" rel="bookmark"/></virtualmachine><utilization><resourceId>23224u230</resourceId><granularity>2</granularity><cpuUserLoad>4.200000e+00</cpuUserLoad><cpuSystemLoad>5.200000e+00</cpuSystemLoad><hostCpuSpeed>2323312</hostCpuSpeed><hostMaxCpuSpeed>92898392838</hostMaxCpuSpeed><ncpus>8</ncpus><diskRead>8.920000e+01</diskRead><diskWrite>2.310000e+01</diskWrite><netRead>8.000000e+01</netRead><netWrite>2.000000e+01</netWrite><totalMemory>24576</totalMemory><freeMemory>8192</freeMemory><uptimeMinute>4820934802</uptimeMinute><reservedSystemCapacity>7423849234</reservedSystemCapacity><maximumSystemCapacity>23479237492839</maximumSystemCapacity><relativeWeight>293472938</relativeWeight><reservedSystemMemory>38929823983</reservedSystemMemory><maximumSystemMemory>2398293832</maximumSystemMemory><memoryRelativeWeight>89239823</memoryRelativeWeight></utilization></VmHost>'
    expected_identifier_show_json = '{"VmHost": {"id": "host-01", "storagevolumes": [{"id": "storage-01", "links": [{"href": "http://localhost:8774/v2.0/storagevolumes/storage-01", "rel": "self"}, {"href": "http://localhost:8774/storagevolumes/storage-01", "rel": "bookmark"}]}, {"id": "storage-02", "links": [{"href": "http://localhost:8774/v2.0/storagevolumes/storage-02", "rel": "self"}, {"href": "http://localhost:8774/storagevolumes/storage-02", "rel": "bookmark"}]}]}}'
    expected_identifier_detail_json = '{"vmhosts": [{"id": "host-01", "storagevolumes": [{"id": "storage-01", "links": [{"href": "http://localhost:8774/v2.0/storagevolumes/storage-01", "rel": "self"}, {"href": "http://localhost:8774/storagevolumes/storage-01", "rel": "bookmark"}]}, {"id": "storage-02", "links": [{"href": "http://localhost:8774/v2.0/storagevolumes/storage-02", "rel": "self"}, {"href": "http://localhost:8774/storagevolumes/storage-02", "rel": "bookmark"}]}]}, {"id": "host-02", "storagevolumes": [{"id": "storage-03", "links": [{"href": "http://localhost:8774/v2.0/storagevolumes/storage-03", "rel": "self"}, {"href": "http://localhost:8774/storagevolumes/storage-03", "rel": "bookmark"}]}, {"id": "storage-04", "links": [{"href": "http://localhost:8774/v2.0/storagevolumes/storage-04", "rel": "self"}, {"href": "http://localhost:8774/storagevolumes/storage-04", "rel": "bookmark"}]}]}]}'
    expected_identifier_show_xml = '<VmHost><id>host-01</id><storagevolume xmlns:atom="http://www.w3.org/2005/Atom" id="storage-01"><atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-01" rel="self"/><atom:link href="http://localhost:8774/storagevolumes/storage-01" rel="bookmark"/></storagevolume><storagevolume xmlns:atom="http://www.w3.org/2005/Atom" id="storage-02"><atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-02" rel="self"/><atom:link href="http://localhost:8774/storagevolumes/storage-02" rel="bookmark"/></storagevolume></VmHost>'
    expected_identifier_detail_xml = '<vmhosts xmlns:atom="http://www.w3.org/2005/Atom" xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0"><VmHost><id>host-01</id><storagevolume id="storage-01"><atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-01" rel="self"/><atom:link href="http://localhost:8774/storagevolumes/storage-01" rel="bookmark"/></storagevolume><storagevolume id="storage-02"><atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-02" rel="self"/><atom:link href="http://localhost:8774/storagevolumes/storage-02" rel="bookmark"/></storagevolume></VmHost><VmHost><id>host-02</id><storagevolume id="storage-03"><atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-03" rel="self"/><atom:link href="http://localhost:8774/storagevolumes/storage-03" rel="bookmark"/></storagevolume><storagevolume id="storage-04"><atom:link href="http://localhost:8774/v2.0/storagevolumes/storage-04" rel="self"/><atom:link href="http://localhost:8774/storagevolumes/storage-04" rel="bookmark"/></storagevolume></VmHost></vmhosts>'

    def setUp(self):
        """ Setup initial mocks and logging configuration """
        super(VmHostsTest, self).setUp()
        self.config_drive = None
        self.mock = mox.Mox()
        self.admin_context = context.RequestContext('admin', '',
                                                    is_admin=True)

    def tearDown(self):
        self.mock.stubs.UnsetAll()

    def test_list_hosts_limited_json(self):
        hosts = self.get_limited_list(3)
        self.mock.StubOutWithMock(api, 'vm_host_get_all_by_filters')
        api.vm_host_get_all_by_filters(mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg()).AndReturn(hosts)
        self.mock.ReplayAll()
        request = webob.Request.blank(
            '/v2.0/vmhosts.json?limit=1&marker=host-1',
            base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().index(request)
        self.assertEqual(self.expected_index_limited_json, resp.body)

    def test_list_hosts_limited_previous_json(self):
        hosts = self.get_limited_list(3)
        self.mock.StubOutWithMock(api, 'vm_host_get_all_by_filters')
        api.vm_host_get_all_by_filters(mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg()).AndReturn(hosts)
        self.mock.ReplayAll()
        request = webob.Request.blank(
            '/v2.0/vmhosts.json?limit=1&marker=host-2',
            base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().index(request)
        self.assertEqual(self.expected_index_limited_previous_json, resp.body)

    def test_list_hosts_json(self):
        hosts = self.get_host_list()
        self.mock.StubOutWithMock(api, 'vm_host_get_all_by_filters')
        api.vm_host_get_all_by_filters(mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg()).AndReturn(hosts)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vmhosts.json',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().index(request)
        self.assertNotEqual(resp, None, 'Return json string')
        self.assertEqual(self.expected_index_json, resp.body)

    def test_list_hosts_detail_xml(self):
        hosts = self.get_host_list()
        self.mock.StubOutWithMock(api, 'vm_host_get_all_by_filters')
        api.vm_host_get_all_by_filters(mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg()).AndReturn(hosts)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vmhosts/detail.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().detail(request)
        self.assertNotEqual(resp, None, 'Return xml string')
        self.assertEqual(resp.body, self.expected_detail_xml)

    def test_list_hosts_none_detail_xml(self):
        hosts = None
        self.mock.StubOutWithMock(api, 'vm_host_get_all_by_filters')
        api.vm_host_get_all_by_filters(mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg()).AndReturn(hosts)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vmhosts/detail.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().detail(request)
        self.assertNotEqual(resp, None, 'Return xml string')

    def test_list_hosts_detail_json(self):
        hosts = self.get_host_list()
        self.mock.StubOutWithMock(api, 'vm_host_get_all_by_filters')
        api.vm_host_get_all_by_filters(mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg()).AndReturn(hosts)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vmhosts/detail',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().detail(request)
        self.assertNotEqual(resp, None)
        self.assertEqual(resp.body, self.expected_detail_json)

    def test_list_hosts_xml(self):
        hosts = self.get_host_list()
        self.mock.StubOutWithMock(api, 'vm_host_get_all_by_filters')
        api.vm_host_get_all_by_filters(mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg()).AndReturn(hosts)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vmhosts.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().index(request)
        self.assertNotEqual(resp, None, 'Return xml string')
        self.assertEqual(resp.body, self.expected_index_xml)

    def test_list_hosts_limited_xml(self):
        hosts = self.get_limited_list(3)
        self.mock.StubOutWithMock(api, 'vm_host_get_all_by_filters')
        api.vm_host_get_all_by_filters(mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg()).AndReturn(hosts)
        self.mock.ReplayAll()
        request = webob.Request.blank(
            '/v2.0/vmhosts.xml?limit=1&marker=host-1',
            base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().index(request)
        self.assertEqual(resp.body, self.expected_index_limited_xml)

    def test_list_hosts_xml_header(self):
        hosts = self.get_host_list()
        self.mock.StubOutWithMock(api, 'vm_host_get_all_by_filters')
        api.vm_host_get_all_by_filters(mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg()).AndReturn(hosts)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vmhosts',
                                      base_url='http://localhost:8774/v2.0/')
        request.headers['Accept'] = 'application/xml'
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().index(request)
        self.assertNotEqual(resp, None, 'Return xml string')
        self.assertEqual(resp.body, self.expected_index_xml)

    def test_list_hosts_json_header(self):
        hosts = self.get_host_list()
        self.mock.StubOutWithMock(api, 'vm_host_get_all_by_filters')
        api.vm_host_get_all_by_filters(mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg()).AndReturn(hosts)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vmhosts',
                                      base_url='http://localhost:8774/v2.0/')
        request.headers['Accept'] = 'application/json'
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().index(request)
        self.assertNotEqual(resp, None, 'Return json string')
        self.assertEqual(self.expected_index_json, resp.body)

    def test_list_vmhost_none_check(self):
        self.mock.StubOutWithMock(api, 'vm_host_get_all_by_filters')
        api.vm_host_get_all_by_filters(mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg()).AndReturn(None)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vmhosts',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().index(request)
        self.assertEqual(resp.body, '{"vmhosts": []}',
                         'Return json string')

    def test_list_host_details_limited_xml(self):
        hosts = self.get_host_list()
        self.mock.StubOutWithMock(api, 'vm_host_get_all_by_filters')
        api.vm_host_get_all_by_filters(mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg()).AndReturn(hosts)
        self.mock.ReplayAll()
        request = webob.Request.blank(
            '/v2.0/vmhosts/detail.xml?limit=1&marker=host-01',
            base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().detail(request)
        self.assertNotEqual(resp, None,
                            'Return xml response detail')
        self.assertEqual(self.expected_detall_limited_previous_xml, resp.body)

    def test_list_host_details_limited_json(self):
        hosts = self.get_host_list()
        self.mock.StubOutWithMock(api, 'vm_host_get_all_by_filters')
        api.vm_host_get_all_by_filters(mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg(),
                                       mox.IgnoreArg()).AndReturn(hosts)
        self.mock.ReplayAll()
        request = webob.Request.blank(
            '/v2.0/vmhosts/detail?limit=1&marker=host-01',
            base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().detail(request)
        self.assertNotEqual(resp, None)
        self.assertEqual(self.expected_detail_limit_marker_json, resp.body)

    def test_host_details_json(self):
        hosts = self.get_single_host()
        self.mock.StubOutWithMock(api, 'vm_host_get_by_ids')

        api.vm_host_get_by_ids(mox.IgnoreArg(),
                               mox.IgnoreArg()).AndReturn(hosts)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vmhosts/host-01.json',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().show(request, 'host-01')
        self.assertNotEqual(resp, None,
                            'Return json response for host-01')
        self.assertEqual(self.expected_limited_detail_json, resp.body)

    def test_host_details_xml(self):
        hosts = self.get_single_host()
        self.mock.StubOutWithMock(api, 'vm_host_get_by_ids')

        api.vm_host_get_by_ids(mox.IgnoreArg(),
                               mox.IgnoreArg()).AndReturn(hosts)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vmhosts/host-01.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().show(request, 'host-01')
        self.assertNotEqual(resp, None,
                            'Return xml response for host-01')
        self.assertEqual(self.expected_detail_limit_marker_xml, resp.body)

    def test_host_details_none_xml(self):
        hosts = None
        self.mock.StubOutWithMock(api, 'vm_host_get_by_ids')

        api.vm_host_get_by_ids(mox.IgnoreArg(),
                               mox.IgnoreArg()).AndReturn(hosts)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vmhosts/host-01.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().show(request, 'host-01')
        self.assertNotEqual(resp, None,
                            'Return xml response for host-01')

    def test_host_details_json_exception(self):
        hosts = self.get_host_list()
        xml_utils = util
        self.mock.StubOutWithMock(xml_utils, 'xml_to_dict')
        xml_utils.xml_to_dict(mox.IgnoreArg()).AndRaise(
            Exception('Test Exception'))
        self.mock.StubOutWithMock(api, 'vm_host_get_by_ids')

        api.vm_host_get_by_ids(mox.IgnoreArg(),
                               mox.IgnoreArg()).AndReturn(hosts)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/vmhosts/host-01.json',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().show(request, 'host-01')
        self.assertTrue(isinstance(resp, HTTPNotFound))

    def test_query_field_key(self):
        hosts = self.get_single_host()
        self.mock.StubOutWithMock(api, 'vm_host_get_by_ids')

        api.vm_host_get_by_ids(mox.IgnoreArg(),
                               mox.IgnoreArg()).AndReturn(hosts)
        self.mock.StubOutWithMock(rpc, 'call')

        rpc.call(mox.IgnoreArg(), mox.IgnoreArg(),
                 mox.IgnoreArg()).AndReturn(self.get_resource_utilization())
        self.mock.ReplayAll()
        request = webob.Request.blank(
            '/v2.0/vmhosts/host-01.json?fields=id,name',
            base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().show(request, 'host-01')
        self.assertNotEqual(resp, None,
                            'Return xml response for host-01')
        self.assertEqual(self.expected_query_id_name, resp.body)
        self.mock.stubs.UnsetAll()

    def test_utilization(self):
        hosts = self.get_single_host()
        self.mock.StubOutWithMock(api, 'vm_host_get_by_ids')

        api.vm_host_get_by_ids(mox.IgnoreArg(),
                               mox.IgnoreArg()).AndReturn(hosts)
        self.mock.StubOutWithMock(rpc, 'call')

        rpc.call(mox.IgnoreArg(), mox.IgnoreArg(),
                 mox.IgnoreArg()).AndReturn(self.get_resource_utilization())
        self.mock.ReplayAll()
        request = webob.Request.blank(
            '/v2.0/vmhosts/host-01.json?fields=utilization',
            base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().show(request, 'host-01')
        self.assertNotEqual(resp, None,
                            'Return xml response for host-01')
        self.assertEqual(self.expected_utilization_json, resp.body)
        self.mock.stubs.UnsetAll()

    def test_utilization_query(self):
        hosts = self.get_single_host()
        self.mock.StubOutWithMock(api, 'vm_host_get_by_ids')

        api.vm_host_get_by_ids(mox.IgnoreArg(),
                               mox.IgnoreArg()).AndReturn(hosts)
        self.mock.StubOutWithMock(rpc, 'call')

        rpc.call(mox.IgnoreArg(), mox.IgnoreArg(),
                 mox.IgnoreArg()).AndReturn(self.get_resource_utilization())
        self.mock.ReplayAll()
        request = \
            webob.Request.blank('/v2.0/vmhosts/host-01.xml?utilization',
                                base_url='http://localhost:8774/v2.0/')

        request.environ['nova.context'] = self.admin_context
        resp = VmHostsController().show(request, 'host-01')
        self.assertNotEqual(resp, None,
                            'Return xml response for host-01')
        self.assertEqual(self.expected_utilization_xml, resp.body)

    def test_vmhost_identifier_json(self):
        request = webob.Request.blank(
            '/v2.0/vmhosts/host-01?fields=storagevolume',
            base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        item_list = self.get_host_list()
        self.assertEquals(
            VmHostsController()._show(request, item_list[0]).body,
            self.expected_identifier_show_json)
        self.assertEquals(
            VmHostsController()._detail(request, item_list, []).body,
            self.expected_identifier_detail_json)

    def test_vmhost_identifier_xml(self):
        request = webob.Request.blank(
            '/v2.0/vmhosts/host-01.xml?fields=storagevolume',
            base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        item_list = self.get_host_list()
        self.assertEquals(
            VmHostsController()._show(request, item_list[0]).body,
            self.expected_identifier_show_xml)
        self.assertEquals(
            VmHostsController()._detail(request, item_list, []).body,
            self.expected_identifier_detail_xml)

    def get_single_host(self):
        host_list = []
        host = VmHost()
        host.set_id('host-01')
        host.set_name('host-01')
        host.add_virtualMachineIds('vm-01')
        host.add_virtualMachineIds('vm-02')
        host.add_storageVolumeIds('storage-01')
        host.add_storageVolumeIds('storage-02')
        host_list.append(host)
        return host_list

    def get_host_list(self):
        host_list = []
        host = VmHost()
        host.set_id('host-01')
        host.set_name('host-01')
        host.add_virtualMachineIds('vm-01')
        host.add_virtualMachineIds('vm-02')
        host.add_storageVolumeIds('storage-01')
        host.add_storageVolumeIds('storage-02')
        host_list.append(host)
        host = VmHost()
        host.set_id('host-02')
        host.set_name('host-02')
        host.add_virtualMachineIds('vm-03')
        host.add_virtualMachineIds('vm-04')
        host.add_storageVolumeIds('storage-03')
        host.add_storageVolumeIds('storage-04')
        host_list.append(host)
        return host_list

    def get_limited_list(self, num):
        host_list = []
        for i in range(1, num + 1):
            host = VmHost()
            host.set_id('host-' + str(i))
            host.set_name('host-' + str(i))
            host.add_virtualMachineIds('vm-' + str(i))
            host.add_virtualMachineIds('vm-' + str(i))
            host.add_storageVolumeIds('storage-' + str(i))
            host.add_storageVolumeIds('storage-' + str(i))
            host_list.append(host)
        return host_list

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


if __name__ == '__main__':

    # import sys;sys.argv = ['', 'Test.testName']

    unittest.main()
