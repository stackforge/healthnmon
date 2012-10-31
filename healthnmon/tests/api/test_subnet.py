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
from webob.exc import HTTPNotFound

from nova import context

from healthnmon.db import api
from healthnmon.api import util
from healthnmon.resourcemodel.healthnmonResourceModel import Subnet
from healthnmon.api.subnet import SubnetController


class SubnetTest(unittest.TestCase):

    """ Tests for Subnet extension """

    expected_limited_detail_xml = '<subnets xmlns:atom="http://www.w3.org/2005/Atom" xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0"><Subnet><id>subnet-02</id><name>subnet-02</name></Subnet><atom:link href="http://localhost:8774/v2.0/subnets?limit=1" rel="previous"/></subnets>'
    expected_detail_xml = '<subnets xmlns:atom="http://www.w3.org/2005/Atom" xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0"><Subnet><id>subnet-01</id><name>subnet-01</name></Subnet><Subnet><id>subnet-02</id><name>subnet-02</name></Subnet></subnets>'
    expected_index_json = '{"subnets": [{"id": "subnet-01", "links": [{"href": "http://localhost:8774/v2.0/subnets/subnet-01", "rel": "self"}, {"href": "http://localhost:8774/subnets/subnet-01", "rel": "bookmark"}], "name": "subnet-01"}, {"id": "subnet-02", "links": [{"href": "http://localhost:8774/v2.0/subnets/subnet-02", "rel": "self"}, {"href": "http://localhost:8774/subnets/subnet-02", "rel": "bookmark"}], "name": "subnet-02"}]}'
    expected_index_detail = '<subnets xmlns:atom="http://www.w3.org/2005/Atom" xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0"><subnet id="subnet-01" name="subnet-01"><atom:link href="http://localhost:8774/v2.0/subnets/subnet-01" rel="self"/><atom:link href="http://localhost:8774/subnets/subnet-01" rel="bookmark"/></subnet><subnet id="subnet-02" name="subnet-02"><atom:link href="http://localhost:8774/v2.0/subnets/subnet-02" rel="self"/><atom:link href="http://localhost:8774/subnets/subnet-02" rel="bookmark"/></subnet></subnets>'
    expected_xml_header = '<subnets xmlns:atom="http://www.w3.org/2005/Atom" xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0"><subnet id="subnet-01" name="subnet-01"><atom:link href="http://localhost:8774/v2.0/subnets/subnet-01" rel="self"/><atom:link href="http://localhost:8774/subnets/subnet-01" rel="bookmark"/></subnet><subnet id="subnet-02" name="subnet-02"><atom:link href="http://localhost:8774/v2.0/subnets/subnet-02" rel="self"/><atom:link href="http://localhost:8774/subnets/subnet-02" rel="bookmark"/></subnet></subnets>'
    expected_json_header = '{"subnets": [{"id": "subnet-01", "links": [{"href": "http://localhost:8774/v2.0/subnets/subnet-01", "rel": "self"}, {"href": "http://localhost:8774/subnets/subnet-01", "rel": "bookmark"}], "name": "subnet-01"}, {"id": "subnet-02", "links": [{"href": "http://localhost:8774/v2.0/subnets/subnet-02", "rel": "self"}, {"href": "http://localhost:8774/subnets/subnet-02", "rel": "bookmark"}], "name": "subnet-02"}]}'
    expected_limited_json = '{"Subnet": {"id": "subnet-01", "name": "subnet-01"}}'
    expected_limited_xml = '<Subnet>\n    <id>subnet-01</id>\n    <name>subnet-01</name>\n</Subnet>\n'

    def setUp(self):
        """ Setup initial mocks and logging configuration """

        super(SubnetTest, self).setUp()
        self.config_drive = None
        self.mock = mox.Mox()
        self.admin_context = context.RequestContext('admin', '',
                is_admin=True)

    def tearDown(self):
        self.mock.stubs.UnsetAll()

    def test_list_subnet_json(self):
        subnet_list = self.get_subnet_list()
        self.mock.StubOutWithMock(api, 'subnet_get_all_by_filters')
        api.subnet_get_all_by_filters(mox.IgnoreArg(),
                                mox.IgnoreArg(),
                                mox.IgnoreArg(),
                                mox.IgnoreArg()).AndReturn(subnet_list)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/subnets.json',
                base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = SubnetController().index(request)
        self.assertNotEqual(resp, None, 'Return json string')
        self.assertEqual(self.expected_index_json, resp.body)
        self.mock.stubs.UnsetAll()

    def test_list_subnet_xml(self):
        subnet_list = self.get_subnet_list()
        self.mock.StubOutWithMock(api, 'subnet_get_all_by_filters')
        api.subnet_get_all_by_filters(mox.IgnoreArg(),
                                mox.IgnoreArg(),
                                mox.IgnoreArg(),
                                mox.IgnoreArg()).AndReturn(subnet_list)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/subnets.xml',
                base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = SubnetController().index(request)
        self.assertNotEqual(resp, None, 'Return xml string')
        self.assertEqual(resp.body, self.expected_index_detail)
        self.mock.stubs.UnsetAll()

    def test_list_limited_subnet_detail_xml(self):
        subnet_list = self.get_subnet_list()
        self.mock.StubOutWithMock(api, 'subnet_get_all_by_filters')
        api.subnet_get_all_by_filters(mox.IgnoreArg(),
                                mox.IgnoreArg(),
                                mox.IgnoreArg(),
                                mox.IgnoreArg()).AndReturn(subnet_list)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/subnets/detail.xml?'
        'limit=1&marker=subnet-01',
                base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = SubnetController().detail(request)
        self.assertEqual(resp.body, self.expected_limited_detail_xml)

    def test_list_subnet_detail_xml(self):
        subnet_list = self.get_subnet_list()
        self.mock.StubOutWithMock(api, 'subnet_get_all_by_filters')
        api.subnet_get_all_by_filters(mox.IgnoreArg(),
                                mox.IgnoreArg(),
                                mox.IgnoreArg(),
                                mox.IgnoreArg()).AndReturn(subnet_list)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/subnets/detail.xml',
                base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = SubnetController().detail(request)
        self.assertEqual(resp.body, self.expected_detail_xml)

    def test_list_subnet_none_detail_xml(self):
        subnet_list = None
        self.mock.StubOutWithMock(api, 'subnet_get_all_by_filters')
        api.subnet_get_all_by_filters(mox.IgnoreArg(),
                                mox.IgnoreArg(),
                                mox.IgnoreArg(),
                                mox.IgnoreArg()).AndReturn(subnet_list)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/subnets/detail.xml',
                base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = SubnetController().detail(request)
        self.assertNotEqual(resp, None, 'Return xml string')

    def test_list_subnet_xml_header(self):
        subnets = self.get_subnet_list()
        self.mock.StubOutWithMock(api, 'subnet_get_all_by_filters')
        api.subnet_get_all_by_filters(mox.IgnoreArg(),
                                mox.IgnoreArg(),
                                mox.IgnoreArg(),
                                mox.IgnoreArg()).AndReturn(subnets)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/subnets',
                base_url='http://localhost:8774/v2.0/')
        request.headers['Accept'] = 'application/xml'
        request.environ['nova.context'] = self.admin_context
        resp = SubnetController().index(request)
        self.assertNotEqual(resp, None, 'Return xml string')
        self.assertEqual(resp.body, self.expected_xml_header)
        self.mock.stubs.UnsetAll()

    def test_list_subnet_json_header(self):
        subnets = self.get_subnet_list()
        self.mock.StubOutWithMock(api, 'subnet_get_all_by_filters')
        api.subnet_get_all_by_filters(mox.IgnoreArg(),
                                mox.IgnoreArg(),
                                mox.IgnoreArg(),
                                mox.IgnoreArg()).AndReturn(subnets)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/subnets',
                base_url='http://localhost:8774/v2.0/')
        request.headers['Accept'] = 'application/json'
        request.environ['nova.context'] = self.admin_context
        resp = SubnetController().index(request)
        self.assertNotEqual(resp, None, 'Return json string')
        self.assertEqual(self.expected_json_header, resp.body)

        self.mock.stubs.UnsetAll()

    def test_list_subnets_none_check(self):
        self.mock.StubOutWithMock(api, 'subnet_get_all_by_filters')
        api.subnet_get_all_by_filters(mox.IgnoreArg(),
                                mox.IgnoreArg(),
                                mox.IgnoreArg(),
                                mox.IgnoreArg()).AndReturn(None)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/subnets',
                base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = SubnetController().index(request)
        self.assertEqual(resp.body, '{"subnets": []}',
                         'Return json string')

    def test_subnet_details_json(self):
        subnet_list = self.get_single_subnet()
        self.mock.StubOutWithMock(api, 'subnet_get_by_ids')

        api.subnet_get_by_ids(mox.IgnoreArg(),
                              mox.IgnoreArg()).AndReturn(subnet_list)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/subnet/subnet-01.json',
                base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = SubnetController().show(request, 'subnet-01')
        self.assertNotEqual(resp, None,
                            'Return json response for subnet-01')
        self.assertEqual(self.expected_limited_json, resp.body)

    def test_subnet_details_xml(self):
        subnet_list = self.get_single_subnet()
        self.mock.StubOutWithMock(api, 'subnet_get_by_ids')

        api.subnet_get_by_ids(mox.IgnoreArg(),
                              mox.IgnoreArg()).AndReturn(subnet_list)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/subnets/subnet-01.xml',
                base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = SubnetController().show(request, 'subnet-01')
        self.assertNotEqual(resp, None,
                            'Return xml response for subnet-01')
        self.assertEqual(self.expected_limited_xml, resp.body)
        self.mock.stubs.UnsetAll()

    def test_subnet_details_none_xml(self):
        subnet_list = None
        self.mock.StubOutWithMock(api, 'subnet_get_by_ids')

        api.subnet_get_by_ids(mox.IgnoreArg(),
                              mox.IgnoreArg()).AndReturn(subnet_list)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/subnets/subnet-01.xml',
                base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = SubnetController().show(request, 'subnet-01')
        self.assertNotEqual(resp, None,
                            'Return xml response for subnet-01')
        self.mock.stubs.UnsetAll()

    def test_subnet_details_json_exception(self):
        subnet_list = self.get_single_subnet()
        xml_utils = util
        self.mock.StubOutWithMock(xml_utils, 'xml_to_dict')
        xml_utils.xml_to_dict(mox.IgnoreArg()).AndRaise(IndexError('Test index'
                ))
        self.mock.StubOutWithMock(api, 'subnet_get_by_ids')

        api.subnet_get_by_ids(mox.IgnoreArg(),
                              mox.IgnoreArg()).AndReturn(subnet_list)
        self.mock.ReplayAll()
        request = webob.Request.blank('/v2.0/subnets/subnet-01.json',
                base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = SubnetController().show(request, 'subnet-01')
        self.assertTrue(isinstance(resp, HTTPNotFound))

    def test_query_field_key(self):
        subnet_list = self.get_single_subnet()
        self.mock.StubOutWithMock(api, 'subnet_get_by_ids')

        api.subnet_get_by_ids(mox.IgnoreArg(),
                              mox.IgnoreArg()).AndReturn(subnet_list)
        self.mock.ReplayAll()
        request = \
            webob.Request.blank(
                    '/v2.0/subnets/subnet-01.json?fields=id,name', \
                    base_url='http://localhost:8774/v2.0/'
                                )
        request.environ['nova.context'] = self.admin_context
        resp = SubnetController().show(request, 'subnet-01')
        self.assertNotEqual(resp, None,
                            'Return xml response for subnet-01')
        self.assertEqual(self.expected_limited_json, resp.body)
        self.mock.stubs.UnsetAll()

    def get_single_subnet(self):
        subnet_list = []
        subnet = Subnet()
        subnet.set_id('subnet-01')
        subnet.set_name('subnet-01')
        subnet_list.append(subnet)
        return subnet_list

    def get_subnet_list(self):
        subnet_list = []
        subnet = Subnet()
        subnet.set_id('subnet-01')
        subnet.set_name('subnet-01')
        subnet_list.append(subnet)
        subnet = Subnet()
        subnet.set_id('subnet-02')
        subnet.set_name('subnet-02')
        subnet_list.append(subnet)
        return subnet_list


if __name__ == '__main__':

    # import sys;sys.argv = ['', 'Test.testName']

    unittest.main()
