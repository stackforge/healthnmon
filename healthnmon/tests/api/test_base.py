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

from fakemodel import FakeModel
from sqlalchemy import exc as sql_exc
from nova.exception import Invalid
from nova import context
from healthnmon.api.base import Controller
from healthnmon.resourcemodel.healthnmonResourceModel import VmHost, IpProfile
from healthnmon.constants import DbConstants


expected_index_json = '{"accounts_links": \
[{"href": "http://marker", "rel": "next"}, \
{"href": "http://marker", "rel": "previous"}], \
"accounts": [{"id": "1", "links": \
[{"href": "http://localhost:8774/v2.0/accounts/1", "rel": "self"}, \
{"href": "http://localhost:8774/accounts/1", \
"rel": "bookmark"}], "name": "name_1"}, \
{"id": "2", "links": [{"href": "http://localhost:8774/v2.0/accounts/2", \
"rel": "self"}, {"href": "http://localhost:8774/accounts/2", \
"rel": "bookmark"}], "name": "name_2"}, {"id": "3", "links": \
[{"href": "http://localhost:8774/v2.0/accounts/3", "rel": "self"}, \
{"href": "http://localhost:8774/accounts/3", "rel": "bookmark"}], \
"name": "name_3"}, {"id": "4", "links": \
[{"href": "http://localhost:8774/v2.0/accounts/4", "rel": "self"}, \
{"href": "http://localhost:8774/accounts/4", "rel": "bookmark"}], \
"name": "name_4"}]}'
expected_index_fields_json = '{"accounts_links": [{"href": "http://marker", \
"rel": "next"}, {"href": "http://marker", "rel": "previous"}], \
"accounts": [{"id": "1", "links": [{"href": \
"http://localhost:8774/v2.0/accounts/1?fields=id", \
"rel": "self"}, {"href": "http://localhost:8774/accounts/1", \
"rel": "bookmark"}], "name": "name_1"}, {"id": "2", "links": \
[{"href": "http://localhost:8774/v2.0/accounts/2?fields=id", \
"rel": "self"}, {"href": "http://localhost:8774/accounts/2", \
"rel": "bookmark"}], "name": "name_2"}, {"id": "3", "links": \
[{"href": "http://localhost:8774/v2.0/accounts/3?fields=id", \
"rel": "self"}, {"href": "http://localhost:8774/accounts/3", \
"rel": "bookmark"}], "name": "name_3"}, {"id": "4", "links": \
[{"href": "http://localhost:8774/v2.0/accounts/4?fields=id", \
"rel": "self"}, {"href": "http://localhost:8774/accounts/4", \
"rel": "bookmark"}], "name": "name_4"}]}'
expected_index_xml = '<accounts xmlns:atom="http://www.w3.org/2005/Atom" \
xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0">\
<account id="1" name="name_1"><atom:link \
href="http://localhost:8774/v2.0/accounts/1" \
rel="self"/><atom:link href="http://localhost:8774/accounts/1" \
rel="bookmark"/></account><account id="2" name="name_2">\
<atom:link href="http://localhost:8774/v2.0/accounts/2" \
rel="self"/><atom:link href="http://localhost:8774/accounts/2" \
rel="bookmark"/></account><account id="3" name="name_3">\
<atom:link href="http://localhost:8774/v2.0/accounts/3" \
rel="self"/><atom:link href="http://localhost:8774/accounts/3" \
rel="bookmark"/></account><account id="4" name="name_4">\
<atom:link href="http://localhost:8774/v2.0/accounts/4" \
rel="self"/><atom:link href="http://localhost:8774/accounts/4" \
rel="bookmark"/></account><atom:link href="http://marker" \
rel="next"/><atom:link href="http://marker" rel="previous"/></accounts>'
expected_index_fields_xml = '<accounts \
xmlns:atom="http://www.w3.org/2005/Atom" \
xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0">\
<account id="1" name="name_1">\
<atom:link href="http://localhost:8774/v2.0/accounts/1?fields=id" \
rel="self"/><atom:link href="http://localhost:8774/accounts/1" \
rel="bookmark"/></account><account id="2" name="name_2">\
<atom:link href="http://localhost:8774/v2.0/accounts/2?fields=id" \
rel="self"/><atom:link href="http://localhost:8774/accounts/2" \
rel="bookmark"/></account><account id="3" name="name_3">\
<atom:link href="http://localhost:8774/v2.0/accounts/3?fields=id" rel="self"/>\
<atom:link href="http://localhost:8774/accounts/3" rel="bookmark"/>\
</account><account id="4" name="name_4"><atom:link \
href="http://localhost:8774/v2.0/accounts/4?fields=id" \
rel="self"/><atom:link href="http://localhost:8774/accounts/4" \
rel="bookmark"/></account><atom:link href="http://marker" rel="next"/>\
<atom:link href="http://marker" rel="previous"/></accounts>'
expected_detail_xml = '<accounts xmlns:atom="http://www.w3.org/2005/Atom" \
xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0"><Account><id>1</id>\
<name>name_1</name></Account><Account><id>2</id><name>name_2</name></Account>\
<Account><id>3</id><name>name_3</name></Account><Account><id>4</id>\
<name>name_4</name></Account><atom:link href="http://marker" rel="next"/>\
<atom:link href="http://marker" rel="previous"/></accounts>'
expected_detail_json = '{"accounts_links": [{"href": "http://marker", \
"rel": "next"}, {"href": "http://marker", "rel": "previous"}], \
"accounts": [{"id": "1", "name": "name_1"}, {"id": "2", "name": "name_2"}, \
{"id": "3", "name": "name_3"}, {"id": "4", "name": "name_4"}]}'
expected_links = "[{'href': 'http://localhost:8774/v2.0/accounts?\
limit=1&marker=3', 'rel': 'next'}, \
{'href': 'http://localhost:8774/v2.0/accounts?limit=1&marker=1', \
'rel': 'previous'}]"
expected_search_json = "({'deleted': 'false'}, 'id', 'desc')"
expected_search_changes_since = "({'deleted': u'f', \
'changes-since': 1336633200000L}, 'createEpoch', 'desc')"
expected_base_show_json = '{"Account": {"id": "1", "name": "name_1"}}'
expected_base_detail_json = '{"accounts": [{"id": "1", "name": "name_1"}, \
{"id": "2", "name": "name_2"}, {"id": "3", "name": "name_3"}, \
{"id": "4", "name": "name_4"}]}'
expected_base_show_xml = '<Account><id>1</id><name>name_1</name></Account>'
expected_base_detail_xml = '<accounts \
xmlns:atom="http://www.w3.org/2005/Atom" \
xmlns="http://docs.openstack.org/ext/healthnmon/api/v2.0"><Account>\
<id>1</id><name>name_1</name></Account><Account><id>2</id><name>name_2</name>\
</Account><Account><id>3</id><name>name_3</name></Account><Account>\
<id>4</id><name>name_4</name></Account></accounts>'


class BaseControllerTest(unittest.TestCase):

    def setUp(self):
        self.controller = Controller('accounts', 'account', 'Account')
        self.admin_context = context.RequestContext('admin', '', is_admin=True)

    def tearDown(self):
        pass

    def test__index_json(self):
        request = webob.Request.blank('/v2.0/accounts.json',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = self.controller._index(
            request,
            [FakeModel(str(x)) for x in range(1, 5)],
            [{'rel': 'next', 'href': 'http://marker'},
             {'rel': 'previous', 'href': 'http://marker'}, ])
        self.assertEquals(expected_index_json, resp.body)

    def test__index_fields_json(self):
        request = webob.Request.blank('/v2.0/accounts.json?fields=id',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = self.controller._index(
            request,
            [FakeModel(str(x)) for x in range(1, 5)],
            [{'rel': 'next', 'href': 'http://marker'},
             {'rel': 'previous', 'href': 'http://marker'}, ])
        self.assertEquals(expected_index_fields_json, resp.body)

    def test__index_xml(self):
        request = webob.Request.blank('/v2.0/accounts.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = self.controller._index(
            request,
            [FakeModel(str(x)) for x in range(1, 5)],
            [{'rel': 'next', 'href': 'http://marker'},
             {'rel': 'previous', 'href': 'http://marker'}, ])
        self.assertEquals(expected_index_xml, resp.body)

    def test__index_fields_xml(self):
        request = webob.Request.blank('/v2.0/accounts.xml?fields=id',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = self.controller._index(
            request,
            [FakeModel(str(x)) for x in range(1, 5)],
            [{'rel': 'next', 'href': 'http://marker'},
             {'rel': 'previous', 'href': 'http://marker'}, ])
        self.assertEquals(expected_index_fields_xml, resp.body)

    def test__detail_json(self):
        request = webob.Request.blank('/v2.0/accounts/detail',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = self.controller._detail(
            request,
            [FakeModel(str(x)) for x in range(1, 5)],
            [{'rel': 'next', 'href': 'http://marker'},
             {'rel': 'previous', 'href': 'http://marker'}, ])
        self.assertEqual(resp.body, expected_detail_json)

    def test__detail_xml(self):
        request = webob.Request.blank('/v2.0/accounts/detail.xml',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = self.controller._detail(
            request,
            [FakeModel(str(x)) for x in range(1, 5)],
            [{'rel': 'next', 'href': 'http://marker'},
             {'rel': 'previous', 'href': 'http://marker'}, ])
        self.assertEqual(resp.body, expected_detail_xml)

    def test_search_options_changes_since(self):
        request = webob.Request.blank(
            '/v2.0/accounts/detail?changes-since=\
2012-05-10T00:00:00&deleted=false',
            base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = self.controller.get_search_options(request, VmHost)
        self.assertNotEqual(resp, None)
        filters = resp[0]
        self.assert_(filters['deleted'] == 'false')
        self.assert_(filters['changes-since'] == 1336608000000)
        sort_key = resp[1]
        self.assert_(sort_key == 'createEpoch')
        sort_dir = resp[2]
        self.assert_(sort_dir == DbConstants.ORDER_DESC)

    def test_search_options_composite(self):
        request = webob.Request.blank(
            '/v2.0/accounts/detail?name=\
SRS&name=SRS111&os=windows&virtualizationType=QEMU',
            base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = self.controller.get_search_options(request, VmHost)
        self.assertNotEqual(resp, None)

    def test_search_options_non_epoc(self):
        request = webob.Request.blank('/v2.0/accounts/detail',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        resp = self.controller.get_search_options(request, IpProfile)
        self.assertNotEqual(resp, None)
        self.assertEqual(str(resp), expected_search_json)

    def test_search_options_exception(self):
        request = webob.Request.blank(
            '/v2.0/accounts/detail?changes-since=ABCD',
            base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self.controller.get_search_options, request, VmHost)

    def test_limited_by_marker(self):
        request = webob.Request.blank('/v2.0/accounts?marker=2&limit=1',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        item_list, collection_links = self.controller.limited_by_marker(
            [FakeModel(
             str(x)) for x in range(1, 5)],
            request)
        self.assertEqual(item_list[0].get_id(), '3')
        self.assertEqual(str(collection_links), expected_links)

    def test_limited_by_marker_exception(self):
        request = webob.Request.blank('/v2.0/accounts?marker=19',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self.controller.limited_by_marker,
                          [FakeModel('1')],
                          request)

    def test_data_error(self):
        def test_func(ctx, filters, sort_key, sort_dir):
            raise sql_exc.DataError('a', 'b', 'c')
        request = webob.Request.blank('/v2.0/accounts?marker=19',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        self.assertRaises(Invalid,
                          Controller('vmhosts',
                                     'vmhost',
                                     'VmHost').get_all_by_filters,
                          request,
                          test_func)

#    Unit tests for defect fix DE84: Healthnmon-API: limit=0 specified in the
#    query gives incorrect result.

    def test_zero_limit_value(self):
        request = webob.Request.blank('/v2.0/accounts?limit=0',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        self.assertEquals(self.controller.limited_by_marker([FakeModel('1')],
                                                            request,
                                                            20),
                          ([], []))

    def test_negative_limit_value(self):
        request = webob.Request.blank('/v2.0/accounts?limit=-1',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        self.assertRaises(webob.exc.HTTPBadRequest,
                          self.controller.limited_by_marker,
                          [FakeModel('1')],
                          request)

#    Unit tests for defect DE86: Healthnmon-API: Add identifier of the
#    resource irrespective of the fields asked( applicable for all resources)

    def test_base_identifier_json(self):
        request = webob.Request.blank('/v2.0/accounts?fields=name',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        item_list = [FakeModel(str(x)) for x in range(1, 5)]
        self.assertEquals(self.controller._show(request, item_list[0]).body,
                          expected_base_show_json)
        self.assertEquals(self.controller._detail(request, item_list, []).body,
                          expected_base_detail_json)

    def test_base_identifier_xml(self):
        request = webob.Request.blank('/v2.0/accounts/detail.xml?fields=name',
                                      base_url='http://localhost:8774/v2.0/')
        request.environ['nova.context'] = self.admin_context
        item_list = [FakeModel(str(x)) for x in range(1, 5)]
        self.assertEquals(self.controller._show(request, item_list[0]).body,
                          expected_base_show_xml)
        self.assertEquals(self.controller._detail(request, item_list, []).body,
                          expected_base_detail_xml)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
