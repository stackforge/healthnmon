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

from nova import context
from healthnmon.db import api
from healthnmon.api import util
from healthnmon.resourcemodel.healthnmonResourceModel import VirtualSwitch
from healthnmon.api.virtualswitch import VirtualSwitchController

from lxml import etree
from lxml import objectify
from StringIO import StringIO


class VirtualSwitchTest(unittest.TestCase):

    """ Tests for virtual switch extension """
    expected_limited_detail_xml = '<virtualswitches \
xmlns:atom="http://www.w3.org/2005/Atom" \
xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0">\
<VirtualSwitch><id>virtual-switch-02</id><name>virtual-switch-02</name>\
<switchType>type-02</switchType><subnet id="subnet-392">\
<atom:link href="http://localhost:8774/v2.0/subnets/subnet-392" rel="self"/>\
<atom:link href="http://localhost:8774/subnets/subnet-392" rel="bookmark"/>\
</subnet></VirtualSwitch>\
<atom:link href="http://localhost:8774/v2.0/virtualswitches?limit=1" \
rel="previous"/></virtualswitches>'
    expected_detail_xml = '<virtualswitches \
xmlns:atom="http://www.w3.org/2005/Atom" \
xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0">\
<VirtualSwitch><id>virtual-switch-01</id><name>virtual-switch-01</name>\
<switchType>type-01</switchType><subnet id="subnet-233">\
<atom:link href="http://localhost:8774/v2.0/subnets/subnet-233" \
rel="self"/><atom:link href="http://localhost:8774/subnets/subnet-233" \
rel="bookmark"/></subnet><subnet id="subnet-03">\
<atom:link href="http://localhost:8774/v2.0/subnets/subnet-03" rel="self"/>\
<atom:link href="http://localhost:8774/subnets/subnet-03" rel="bookmark"/>\
</subnet></VirtualSwitch><VirtualSwitch><id>virtual-switch-02</id>\
<name>virtual-switch-02</name><switchType>type-02</switchType>\
<subnet id="subnet-392"><atom:link \
href="http://localhost:8774/v2.0/subnets/subnet-392" rel="self"/>\
<atom:link href="http://localhost:8774/subnets/subnet-392" rel="bookmark"/>\
</subnet></VirtualSwitch></virtualswitches>'

    def setUp(self):
        """ Setup initial mocks and logging configuration """

        super(VirtualSwitchTest, self).setUp()
        self.config_drive = None
        self.mock = mox.Mox()
        self.admin_context = context.RequestContext('admin', '',
                                                    is_admin=True)

    def tearDown(self):
        self.mock.stubs.UnsetAll()

    def test_list_virtual_switch_json(self):
        expected_out_json = '{"virtualswitches": [{"id": "virtual-switch-01", \
"links": [{"href": \
"http://localhost:8774/v2.0/virtualswitches/virtual-switch-01", \
"rel": "self"}, {"href": \
"http://localhost:8774/virtualswitches/virtual-switch-01", \
"rel": "bookmark"}], "name": "virtual-switch-01"}, \
{"id": "virtual-switch-02", "links": \
[{"href": "http://localhost:8774/v2.0/virtualswitches/virtual-switch-02", \
"rel": "self"}, {"href": \
"http://localhost:8774/virtualswitches/virtual-switch-02", \
"rel": "bookmark"}], "name": "virtual-switch-02"}]}'

        virtual_switch_list = self.get_virtual_switch_list()
        self.mock.StubOutWithMock(api, 'virtual_switch_get_all_by_filters')
        api.virtual_switch_get_all_by_filters(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            mox.IgnoreArg()).AndReturn(virtual_switch_list)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/virtualswitches.json',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VirtualSwitchController().index(request)
        self.assertNotEqual(resp, None, 'Return json string')
        self.compare_json(expected_out_json, resp.body)

#        self.assertEqual(self.expected_index_json, resp.body)

        self.mock.stubs.UnsetAll()

    def test_list_virtual_switch_xml(self):
        expected_out_xml = '<virtualswitches \
xmlns:atom="http://www.w3.org/2005/Atom" \
xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0">\
<virtualswitch id="virtual-switch-01" name="virtual-switch-01">\
<atom:link \
href="http://localhost:8774/v2.0/virtualswitches/virtual-switch-01" \
rel="self"/>\
<atom:link href="http://localhost:8774/virtualswitches/virtual-switch-01" \
rel="bookmark"/>\
</virtualswitch><virtualswitch id="virtual-switch-02" \
name="virtual-switch-02">\
<atom:link \
href="http://localhost:8774/v2.0/virtualswitches/virtual-switch-02" \
rel="self"/>\
<atom:link href="http://localhost:8774/virtualswitches/virtual-switch-02" \
rel="bookmark"/>\
</virtualswitch></virtualswitches>'

        virtual_switch_list = self.get_virtual_switch_list()
        self.mock.StubOutWithMock(api, 'virtual_switch_get_all_by_filters')
        api.virtual_switch_get_all_by_filters(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            mox.IgnoreArg()).AndReturn(virtual_switch_list)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/virtualswitches.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VirtualSwitchController().index(request)
        self.assertNotEqual(resp, None, 'Return xml string')
        self.compare_xml(expected_out_xml, resp.body)

#        self.assertEqual(resp.body, self.expected_index_xml)

        self.mock.stubs.UnsetAll()

    def test_list_virtual_switch_xml_header(self):
        expected_out_xml = '<virtualswitches \
xmlns:atom="http://www.w3.org/2005/Atom" \
xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0">\
<virtualswitch id="virtual-switch-01" name="virtual-switch-01">\
<atom:link \
href="http://localhost:8774/v2.0/virtualswitches/virtual-switch-01" \
rel="self"/>\
<atom:link href="http://localhost:8774/virtualswitches/virtual-switch-01" \
rel="bookmark"/>\
</virtualswitch><virtualswitch id="virtual-switch-02" \
name="virtual-switch-02">\
<atom:link \
href="http://localhost:8774/v2.0/virtualswitches/virtual-switch-02" \
rel="self"/>\
<atom:link href="http://localhost:8774/virtualswitches/virtual-switch-02" \
rel="bookmark"/>\
</virtualswitch></virtualswitches>'

        virtual_switches = self.get_virtual_switch_list()
        self.mock.StubOutWithMock(api, 'virtual_switch_get_all_by_filters')
        api.virtual_switch_get_all_by_filters(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            mox.IgnoreArg()).AndReturn(virtual_switches)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/virutalswitches',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        request.headers['Accept'] = 'application/xml'
        resp = VirtualSwitchController().index(request)
        self.assertNotEqual(resp, None, 'Return xml string')
        self.compare_xml(expected_out_xml, resp.body)

#        self.assertEqual(resp.body, self.expected_index_xml)

        self.mock.stubs.UnsetAll()

    def test_list_virtual_switch_json_header(self):
        expected_out_json = '{"virtualswitches": [{"id": "virtual-switch-01", \
"links": [{"href": \
"http://localhost:8774/v2.0/virtualswitches/virtual-switch-01", \
"rel": "self"}, {"href": \
"http://localhost:8774/virtualswitches/virtual-switch-01", \
"rel": "bookmark"}], "name": "virtual-switch-01"}, \
{"id": "virtual-switch-02", "links": [{"href": \
"http://localhost:8774/v2.0/virtualswitches/virtual-switch-02", \
"rel": "self"},{"href": \
"http://localhost:8774/virtualswitches/virtual-switch-02", \
"rel": "bookmark"}], "name": "virtual-switch-02"}]}'

        virtual_switches = self.get_virtual_switch_list()
        self.mock.StubOutWithMock(api, 'virtual_switch_get_all_by_filters')
        api.virtual_switch_get_all_by_filters(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            mox.IgnoreArg()).AndReturn(virtual_switches)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/virtualswitches',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        request.headers['Accept'] = 'application/json'
        resp = VirtualSwitchController().index(request)
        self.assertNotEqual(resp, None, 'Return json string')
        self.compare_json(expected_out_json, resp.body)

#        self.assertEqual(self.expected_index_json, resp.body)

        self.mock.stubs.UnsetAll()

    def test_list_limited_virtual_switch_detail_xml(self):
        virtual_switches = self.get_virtual_switch_list()
        self.mock.StubOutWithMock(api, 'virtual_switch_get_all_by_filters')
        api.virtual_switch_get_all_by_filters(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            mox.IgnoreArg()).AndReturn(virtual_switches)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/virtualswitches/detail.xml?'
                                      'limit=1&marker=virtual-switch-01',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VirtualSwitchController().detail(request)
        self.assertEqual(resp.body, self.expected_limited_detail_xml)

    def test_list_virtual_switch_detail_xml(self):
        virtual_switches = self.get_virtual_switch_list()
        self.mock.StubOutWithMock(api, 'virtual_switch_get_all_by_filters')
        api.virtual_switch_get_all_by_filters(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            mox.IgnoreArg()).AndReturn(virtual_switches)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/virtualswitches/detail.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VirtualSwitchController().detail(request)
        self.assertEqual(resp.body, self.expected_detail_xml)

    def test_list_virtual_switch_detail_none_xml(self):
        virtual_switches = None
        self.mock.StubOutWithMock(api, 'virtual_switch_get_all_by_filters')
        api.virtual_switch_get_all_by_filters(
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            mox.IgnoreArg(),
            mox.IgnoreArg()).AndReturn(virtual_switches)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/virtualswitches/detail.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VirtualSwitchController().detail(request)
        self.assertNotEqual(resp, None, 'Return xml string')

    def test_list_virtual_switch_none_check(self):
        self.mock.StubOutWithMock(api, 'virtual_switch_get_all_by_filters')
        api.virtual_switch_get_all_by_filters(mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg(),
                                              mox.IgnoreArg()).AndReturn(None)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/virtualswitches',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VirtualSwitchController().index(request)
        self.assertEqual(resp.body, '{"virtualswitches": []}',
                         'Return json string')

    def test_virtual_switch_details_json(self):
        expected_out_json = '{"VirtualSwitch": {"subnets": [{"id": \
"subnet-3883", "links": [{"href": \
"http://localhost:8774/v2.0/subnets/subnet-3883", "rel": "self"}, \
{"href": "http://localhost:8774/subnets/subnet-3883", "rel": "bookmark"}]}, \
{"id": "subnet-323", "links": [{"href": \
"http://localhost:8774/v2.0/subnets/subnet-323", "rel": "self"}, \
{"href": "http://localhost:8774/subnets/subnet-323", \
"rel": "bookmark"}]}], "id": "virtual-switch-01", \
"switchType": "dvSwitch", "name": "virtual-switch-01"}}'

        virtual_switch_list = self.get_single_virtual_switch()
        self.mock.StubOutWithMock(api, 'virtual_switch_get_by_ids')

        api.virtual_switch_get_by_ids(
            mox.IgnoreArg(),
            mox.IgnoreArg()).AndReturn(virtual_switch_list)
        self.mock.ReplayAll()
        request = \
            webob.Request.blank(
                '/v2.0/virtualswitches/virtual-switch-01.json',
                base_url='http://localhost:8774/v2.0/'
            )
        request.environ['nova.context'] = self.admin_context
        resp = VirtualSwitchController().show(request,
                                              'virtual-switch-01')
        self.assertNotEqual(resp, None,
                            'Return json response for virtual-switch-01'
                            )
        self.mock.stubs.UnsetAll()
        self.compare_json(expected_out_json, resp.body)

    def test_virtual_switch_details_xml(self):
        expected_out_xml = '<VirtualSwitch><id>virtual-switch-01</id>\
<name>virtual-switch-01</name><switchType>dvSwitch</switchType>\
<subnet xmlns:atom="http://www.w3.org/2005/Atom" id="subnet-3883">\
<atom:link href="http://localhost:8774/v2.0/subnets/subnet-3883" rel="self"/>\
<atom:link href="http://localhost:8774/subnets/subnet-3883" rel="bookmark"/>\
</subnet>\
<subnet xmlns:atom="http://www.w3.org/2005/Atom" id="subnet-323">\
<atom:link href="http://localhost:8774/v2.0/subnets/subnet-323" rel="self"/>\
<atom:link href="http://localhost:8774/subnets/subnet-323" rel="bookmark"/>\
</subnet></VirtualSwitch>'

        virtual_switch_list = self.get_single_virtual_switch()
        self.mock.StubOutWithMock(api, 'virtual_switch_get_by_ids')

        api.virtual_switch_get_by_ids(
            mox.IgnoreArg(),
            mox.IgnoreArg()).AndReturn(virtual_switch_list)
        self.mock.ReplayAll()
        request = \
            webob.Request.blank(
                '/v2.0/virtualswitches/virtual-switch-01.xml',
                base_url='http://localhost:8774/v2.0/'
            )
        request.environ['nova.context'] = self.admin_context
        resp = VirtualSwitchController().show(request,
                                              'virtual-switch-01')
        self.assertNotEqual(resp, None,
                            'Return xml response for virtual-switch-01')
        self.compare_xml(expected_out_xml, resp.body)
        self.mock.stubs.UnsetAll()

    def test_virtual_switch_none_details_xml(self):
        virtual_switch_list = None
        self.mock.StubOutWithMock(api, 'virtual_switch_get_by_ids')

        api.virtual_switch_get_by_ids(
            mox.IgnoreArg(),
            mox.IgnoreArg()).AndReturn(virtual_switch_list)
        self.mock.ReplayAll()
        request = \
            webob.Request.blank(
                '/v2.0/virtualswitches/virtual-switch-01.xml',
                base_url='http://localhost:8774/v2.0/'
            )
        request.environ['nova.context'] = self.admin_context
        resp = VirtualSwitchController().show(request,
                                              'virtual-switch-01')
        self.assertNotEqual(resp, None,
                            'Return xml response for virtual-switch-01')
        self.mock.stubs.UnsetAll()

    def test_virtual_switch_details_json_exception(self):
        virtual_switch_list = self.get_single_virtual_switch()
        xml_utils = util
        self.mock.StubOutWithMock(xml_utils, 'xml_to_dict')
        xml_utils.xml_to_dict(mox.IgnoreArg()).AndRaise(IndexError('Test index'
                                                                   ))
        self.mock.StubOutWithMock(api, 'virtual_switch_get_by_ids')

        api.virtual_switch_get_by_ids(
            mox.IgnoreArg(),
            mox.IgnoreArg()).AndReturn(virtual_switch_list)
        self.mock.ReplayAll()
        request = \
            webob.Request.blank(
                '/v2.0/virtualswitches/virtual-switch-01.json',
                base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VirtualSwitchController().show(request, 'virtual-switch-01')
        self.assertTrue(isinstance(resp, HTTPNotFound))

    def test_query_field_key(self):
        expected_out_json = '{"VirtualSwitch": {"id": "virtual-switch-01", \
"name": "virtual-switch-01"}}'

        virtual_switch_list = self.get_single_virtual_switch()
        self.mock.StubOutWithMock(api, 'virtual_switch_get_by_ids')

        api.virtual_switch_get_by_ids(
            mox.IgnoreArg(), mox.IgnoreArg()).AndReturn(virtual_switch_list)
        self.mock.ReplayAll()
        request = \
            webob.Request.blank('/v2.0/vm/vm-01.json?fields=id,name',
                                base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = VirtualSwitchController().show(request, 'virtual-switch-01')
        self.assertNotEqual(resp, None,
                            'Return xml response for virtual-switch-01')
        self.compare_json(expected_out_json, resp.body)
        self.mock.stubs.UnsetAll()

    def get_single_virtual_switch(self):
        virtual_switch_list = []
        virtual_switch = VirtualSwitch()
        virtual_switch.set_id('virtual-switch-01')
        virtual_switch.set_name('virtual-switch-01')
        virtual_switch.set_switchType('dvSwitch')
        virtual_switch.add_subnetIds('subnet-3883')
        virtual_switch.add_subnetIds('subnet-323')
        virtual_switch_list.append(virtual_switch)
        return virtual_switch_list

    def get_virtual_switch_list(self):
        virtual_switch_list = []
        virtual_switch = VirtualSwitch()
        virtual_switch.set_id('virtual-switch-01')
        virtual_switch.set_name('virtual-switch-01')
        virtual_switch.set_switchType('type-01')
        virtual_switch.add_subnetIds('subnet-233')
        virtual_switch.add_subnetIds('subnet-03')
        virtual_switch_list.append(virtual_switch)
        virtual_switch = VirtualSwitch()
        virtual_switch.set_id('virtual-switch-02')
        virtual_switch.set_name('virtual-switch-02')
        virtual_switch.set_switchType('type-02')
        virtual_switch.add_subnetIds('subnet-392')
        virtual_switch_list.append(virtual_switch)
        return virtual_switch_list

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
