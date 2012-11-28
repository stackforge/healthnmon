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

from healthnmon.api import constants
from healthnmon.api import util
from nova import context
from healthnmon.resourcemodel import healthnmonResourceModel

import json
import unittest
from webob import BaseRequest, Request

from lxml import etree
from lxml import objectify


class UtilTest(unittest.TestCase):

    def setUp(self):
        super(UtilTest, self).setUp()

    def tearDown(self):
        pass

    def test_xml_to_dict(self):
        test_xml = \
            """<VmHost>
                    <id>VH1</id>
                    <name>host1</name>
                    <note>some other note</note>
                    <processorCoresCount>6</processorCoresCount>
                    <properties>
                        <name>prop1</name>
                        <value>value1</value>
                    </properties>
                    <properties>
                        <name>prop2</name>
                        <value>value2</value>
                    </properties>

                    <os>
                        <osType>LINUX</osType>
                        <osSubType>UBUNTU</osSubType>
                        <osVersion>11.0</osVersion>
                    </os>
                    <model>model1</model>
                    <virtualizationType>KVM</virtualizationType>
                </VmHost>"""
        expected_host_json = \
            '{"virtualizationType": "KVM", "name": "host1", \
"processorCoresCount": "6", "id": "VH1", "note": "some other note", \
"model": "model1", "os": {"osType": "LINUX", "osSubType": "UBUNTU", \
"osVersion": "11.0"}, "properties": [{"name": "prop1", "value": "value1"}, \
{"name": "prop2", "value": "value2"}]}'
        test_dict = util.xml_to_dict(test_xml)
        json_str = json.dumps(test_dict)
        print json_str
        self.assertEquals(json_str, expected_host_json)

    def test_replace_with_links(self):
        test_xml = \
            """<Vm><outer><a><storage><id>33</id><name>ESA</name>
                    </storage></a></outer>
                    <storageVolumeId>88</storageVolumeId>
                    <storageVolumeId>89</storageVolumeId>
                    <parent>
                        <id>89</id>
                        <name>testname</name>
                        <type>human</type>
                    </parent>
                    </Vm>"""

        expected_out_xml = \
            '<Vm><outer><a><storage><id>33</id><name>ESA</name></storage></a></outer>\
       <storagevolume xmlns:atom="http://www.w3.org/2005/Atom" id="88">\
       <atom:link href="http://localhost/v2.0/storage/88" rel="self"/><atom:link href="http://localhost/storage/88" rel="bookmark"/>\
       </storagevolume>\
       <storagevolume xmlns:atom="http://www.w3.org/2005/Atom" id="89">\
       <atom:link href="http://localhost/v2.0/storage/89" rel="self"/><atom:link href="http://localhost/storage/89" rel="bookmark"/>\
       </storagevolume>\
       <person xmlns:atom="http://www.w3.org/2005/Atom" name="testname" type="human" id="89">\
       <atom:link href="http://localhost/v2.0/people/89" rel="self"/><atom:link href="http://localhost/people/89" rel="bookmark"/>\
       </person></Vm>'

        dict_tag_props = [{
            'tag': 'storageVolumeId',
            'tag_replacement': 'storagevolume',
            'tag_key': 'id',
            'tag_collection_url': 'http://localhost/v2.0/storage',
            'tag_attrib': None,
        }, {
            'tag': 'vmHostId',
            'tag_replacement': 'vmhosts',
            'tag_key': 'id',
            'tag_collection_url': 'http://localhost/v2.0/vmhosts',
            'tag_attrib': None,
        }, {
            'tag': 'parent',
            'tag_replacement': 'person',
            'tag_key': 'id',
            'tag_collection_url': 'http://localhost/v2.0/people',
            'tag_attrib': ['name', 'type'],
        }]

#        element = util.replace_with_references(test_xml, dict_tag_props)

        out_dict = {}
        replaced_xml = util.replace_with_links(test_xml,
                                               dict_tag_props, out_dict)
        self.assertNotEqual(None, replaced_xml)
        self.compare_xml(expected_out_xml, replaced_xml)

        #        print element.toxml('utf-8')

    def test_xml_to_dict_with_collections(self):
        input_xml = '<Vm><outer><a><storage><id>33</id><name>ESA</name></storage></a></outer>\
        <storagevolume xmlns:atom="http://www.w3.org/2005/Atom" id="88">\
        <atom:link href="http://localhost/v2.0/storage/88" rel="self"/><atom:link href="http://localhost/storage/88" rel="bookmark"/>\
        </storagevolume>\
        <storagevolume xmlns:atom="http://www.w3.org/2005/Atom" id="89">\
        <atom:link href="http://localhost/v2.0/storage/89" rel="self"/><atom:link href="http://localhost/storage/89" rel="bookmark"/>\
        </storagevolume>\
        <person xmlns:atom="http://www.w3.org/2005/Atom" name="testname" type="human" id="89">\
        <atom:link href="http://localhost/v2.0/people/89" rel="self"/><atom:link href="http://localhost/people/89" rel="bookmark"/>\
        </person></Vm>'
        expected_json = '{"person": {"links": [{"href": "http://localhost/v2.0/people/89", "rel": "self"}, {"href": "http://localhost/people/89", "rel": "bookmark"}]}, "outer": {"a": {"storage": {"id": "33", "name": "ESA"}}}, "storagevolumes": [{"id": "88", "links": [{"href": "http://localhost/v2.0/storage/88", "rel": "self"}, {"href": "http://localhost/storage/88", "rel": "bookmark"}]}, {"id": "89", "links": [{"href": "http://localhost/v2.0/storage/89", "rel": "self"}, {"href": "http://localhost/storage/89", "rel": "bookmark"}]}]}'
        self.assertEquals(
            json.dumps(util.xml_to_dict(input_xml)), expected_json)

    def test_replace_with_links_prefix(self):
        prefix_xml = \
            '<p:Vm xmlns:p="http://localhost/prefix"><p:outer><p:a><p:storage>\
        <p:id>33</p:id><p:name>ESA</p:name></p:storage></p:a></p:outer>\
        <p:storageVolumeId>88</p:storageVolumeId>\
        <p:storageVolumeId>89</p:storageVolumeId></p:Vm>'

        dict_tag_props = [{
            'tag': 'storageVolumeId',
            'tag_replacement': 'storagevolume',
            'tag_key': 'id',
            'tag_collection_url': 'http://localhost/v2.0/storage',
            'tag_attrib': None,
        }, {
            'tag': 'vmHostId',
            'tag_replacement': 'vmhosts',
            'tag_key': 'id',
            'tag_collection_url': 'http://localhost/v2.0/vmhosts',
            'tag_attrib': None,
        }]

        expected_out_xml = \
            '<p:Vm xmlns:p="http://localhost/prefix">\
        <p:outer>\
        <p:a><p:storage><p:id>33</p:id><p:name>ESA</p:name></p:storage></p:a>\
        </p:outer>\
        <p:storagevolume xmlns:atom="http://www.w3.org/2005/Atom" p:id="88">\
        <atom:link href="http://localhost/v2.0/storage/88" rel="self"/>\
        <atom:link href="http://localhost/storage/88" rel="bookmark"/>\
        </p:storagevolume>\
        <p:storagevolume xmlns:atom="http://www.w3.org/2005/Atom" p:id="89">\
        <atom:link href="http://localhost/v2.0/storage/89" rel="self"/>\
        <atom:link href="http://localhost/storage/89" rel="bookmark"/>\
        </p:storagevolume>\
        </p:Vm>'

        out_dict = {}
        replaced_xml = util.replace_with_links(prefix_xml,
                                               dict_tag_props, out_dict)
        self.assertNotEqual(None, replaced_xml)
        self. compare_xml(expected_out_xml, replaced_xml)

    def test_xml_with_no_children_to_dict(self):
        xml_str = '<tag></tag>'
        test_dict = util.xml_to_dict(xml_str)
        self.assertEquals(test_dict, None)

    def test_get_path_elements(self):
        expected_list = ['', 'parent', 0]
        obtained_list = []
        for element in util.get_path_elements('/parent[1]'):
            obtained_list.append(element)
        self.assertEquals(expected_list, obtained_list,
                          'get path elements')

    def test_get_project_context(self):
        test_context = context.RequestContext('user', 'admin', is_admin=True)
        req = BaseRequest({'nova.context': test_context})
        (ctx, proj_id) = util.get_project_context(req)
        self.assertEquals(ctx, test_context, 'Context test util')
        self.assertEquals(proj_id, 'admin')

#    def test_remove_version_from_href(self):
#        common.remove_version_from_href( \
#         'http://10.10.120.158:8774/v2/virtualmachines/\
#e9f7f71d-8208-1963-77fc-a1c90d4a1802'
#                )
#        try:
#            common.remove_version_from_href('http://localhost/')
#        except ValueError, err:
#            print err
#        else:
#            self.fail('No Value Error thrown when removing version number'
#                      )

    def test_invalid_dict(self):
        prefix_xml = \
            '<p:Vm xmlns:p="http://localhost/prefix"><p:outer><p:a><p:storage>\
<p:id>33</p:id><p:name>ESA</p:name></p:storage></p:a></p:outer>\
<p:storageVolumeId>88</p:storageVolumeId>\
<p:storageVolumeId>89</p:storageVolumeId></p:Vm>'

        dict_tag_props = [{
            'tag': 'storageVolumeId',
            'tag_key': 'id',
            'tag_collection_url': 'http://localhost/v2.0/storage',
            'tag_attrib': None,
        }]

        replaced_xml = util.replace_with_links(prefix_xml,
                                               dict_tag_props, {})
        print replaced_xml
        self.assertNotEqual(None, replaced_xml)
        self.assertEqual(util.replace_with_links(prefix_xml, [None],
                         {}), prefix_xml)
        dict_tag_props = [{
            'tag': 'storageVolumeId',
            'tag_key': 'id',
            'tag_collection_url': 'http://localhost/v2.0/storage',
            'tag_attrib': None,
            3.23: 32,
        }]

        util.replace_with_links(prefix_xml, dict_tag_props, {})

    def test_none_dict(self):
        xml_str = '<test>value</test>'
        self.assertEquals(xml_str, util.replace_with_links(xml_str,
                          None, {}))
        self.assertEquals(xml_str, util.replace_with_links(xml_str,
                          [{None: None}], {}))

#    def test_single_element(self):
#        xml_str = '<test>value</test>'
#        dict_tag_props = [{
#            'tag': 'test',
#            'tag_replacement': None,
#            'tag_key': 'key',
#            'tag_collection_url': 'http://localhost/v2.0/collection',
#            'tag_attrib': None,
#            }]
#
#        replaced_xml = util.replace_with_links(xml_str, dict_tag_props,
#                {})
#        expected_xml = \
#            '<test xmlns:atom="http://www.w3.org/2005/Atom key="value">\
#<atom:link href="http://localhost/v2.0/collection/value" rel="self"/>\
#<atom:link href="http://localhost/collection/value" rel="bookmark"/></test>'
#
#        self.assertNotEqual(replaced_xml, xml_str)

    def test_tag_dictionary_error(self):
        xml_str = '<test xmlns="http://localhost/name"></test>'
        dict_tag_props = [{
            'tag': 'test',
            'tag_replacement': None,
            'tag_key': 'key',
            'tag_collection_url': 'http://localhost/v2.0/collection',
            'tag_attrib': None,
        }]

        try:
            util.replace_with_links(xml_str, dict_tag_props, {})
        except util.TagDictionaryError, err:
            print err
        else:
            self.fail('TagDictionary Error not thrown for xml: %s'
                      % xml_str)

    def test_update_dict_using_xpath(self):
        xpath_dict = {'/mypath[1]/element': [1, 2, 3]}
        expected_dict = {'mypath': [{'element': [1, 2, 3]}]}

        input_dict = {'mypath': [{'element': [4, 5, 6]}]}

        util.update_dict_using_xpath(input_dict, xpath_dict)
        self.assertEquals(input_dict, expected_dict)
        self.assertEquals(None, util.update_dict_using_xpath(None,
                          None))
        self.assertEquals(input_dict,
                          util.update_dict_using_xpath(input_dict,
                          None))

    def test_serialize_simple_obj(self):

        class Test:

            def __init__(self):
                self.a = 10
                self.b = None

        self.assertEquals(util.serialize_simple_obj(Test(), 'root', ('a',
                          'b')), '<root><a>10</a><b></b></root>')
        self.assertEquals(util.serialize_simple_obj(Test(), 'root', 'c'
                                                    ), '<root><c/></root>')

    def test_append_xml_as_child(self):
        xml = '<root>212</root>'
        xml = util.append_xml_as_child(xml, '<sub>23</sub>')
        print xml
        self.assertEquals(util.append_xml_as_child('<root><a>3</a></root>',
                          '<a>4</a>'), '<root><a>3</a><a>4</a></root>'
                          )

    def test_get_entity_list_xml(self):
        entity_list = []
        expected_list_xml = \
            '<b:entities xmlns:b="http://testnamespace" \
xmlns:atom="http://www.w3.org/2005/Atom"><b:entity type="" id="0">\
<atom:link href="http://localhost:8080/v2/entities/0" rel="self"/>\
<atom:link href="http://localhost:8080/entities/0" rel="bookmark"/></b:entity>\
<b:entity type="" id="1">\
<atom:link href="http://localhost:8080/v2/entities/1" rel="self"/>\
<atom:link href="http://localhost:8080/entities/1" rel="bookmark"/>\
</b:entity><atom:link href="http://markerlink" rel="next"/></b:entities>'

        for i in range(2):
            href = 'http://localhost:8080/v2/entities/' + str(i)
            bookmark = 'http://localhost:8080/entities/' + str(i)
            entdict = {'id': str(i), 'type': None,
                       'links': [{'rel': 'self', 'href': href},
                       {'rel': 'bookmark', 'href': bookmark}],
                       }
            entity_list.append(entdict)
        entities_dict = dict(entities=entity_list)
        entities_dict['entities_links'] = [
            {
                'rel': 'next',
                'href': 'http://markerlink'
            }
        ]
        self.assertEquals(util.get_entity_list_xml(entities_dict,
                          {'b': 'http://testnamespace',
                          'atom': constants.XMLNS_ATOM}, 'entities',
                          'entity', 'b'), expected_list_xml)
        try:
            util.get_entity_list_xml({'a': 23, 'b': 23}, None, None,
                                     None)
        except Exception, inst:
            self.assertTrue(isinstance(inst, LookupError))
        self.assertEquals(util.get_entity_list_xml(None, None, None,
                          None), '')
        self.assertEquals(util.get_entity_list_xml({}, None, None,
                          None), '')
        self.assertEquals(util.get_entity_list_xml({'abcd': [None]},
                          None, 'abcd', None), '<abcd/>')

    def test_get_query_fields(self):
        req = \
            Request.blank('/test?fields=a,b&fields=utilization&fields=')
        self.assertEquals(util.get_query_fields(req), ['a', 'b',
                          'utilization'])

    def test_get_select_elements_xml(self):
        input_xml = \
            '<outer xmlns="http://space/noprefix"><a><sub>32</sub></a>\
<b>83</b><c>32</c></outer>'
        self.assertEquals(util.get_select_elements_xml(input_xml, ['a',
                          'c']),
                          '<outer xmlns="http://space/noprefix">\
<a><sub>32</sub></a><c>32</c></outer>'
                          )
        prefix_xml = \
            '<p:Vm xmlns:p="http://localhost/prefix"><p:outer><p:a><p:storage>\
<p:id>33</p:id><p:name>ESA</p:name></p:storage></p:a></p:outer>\
<p:storageVolumeId>88</p:storageVolumeId>\
<p:storageVolumeId>89</p:storageVolumeId></p:Vm>'

#        self.assertEquals(util.get_select_elements_xml(prefix_xml, ['a']),
#                          '<outer><a><sub>32</sub></a><c>32</c></outer>')

        self.assertEquals('<p:Vm xmlns:p="http://localhost/prefix">\
<p:outer><p:a><p:storage><p:id>33</p:id>\
<p:name>ESA</p:name></p:storage></p:a></p:outer></p:Vm>',
                          util.get_select_elements_xml(prefix_xml,
                          ['outer']))

    def test_get_select_elements_xml_default_field(self):
        input_xml = \
            '<outer xmlns="http://space/noprefix"><a><sub>32</sub></a>\
<b>83</b><c>32</c></outer>'
        self.assertEquals(util.get_select_elements_xml(input_xml, ['a',
                          'c']),
                          '<outer xmlns="http://space/noprefix">\
<a><sub>32</sub></a><c>32</c></outer>'
                          )
        self.assertEquals(util.get_select_elements_xml(input_xml, ['c'], 'b'),
                          '<outer xmlns="http://space/noprefix"><b>83</b><c>32</c></outer>')
        prefix_xml = \
            '<p:Vm xmlns:p="http://localhost/prefix"><p:outer><p:a><p:storage>\
<p:id>33</p:id><p:name>ESA</p:name></p:storage></p:a></p:outer>\
<p:storageVolumeId>88</p:storageVolumeId>\
<p:storageVolumeId>89</p:storageVolumeId></p:Vm>'
        self.assertEquals(
            '<p:Vm xmlns:p="http://localhost/prefix"><p:storageVolumeId>88</p:storageVolumeId><p:storageVolumeId>89</p:storageVolumeId><p:outer><p:a><p:storage><p:id>33</p:id><p:name>ESA</p:name></p:storage></p:a></p:outer></p:Vm>',
            util.get_select_elements_xml(prefix_xml,
                                         ['outer'], 'storageVolumeId'))

    def test_set_select_attributes(self):
        resource_obj = healthnmonResourceModel.ResourceUtilization()
        self.assertEquals(resource_obj,
                          util.set_select_attributes(resource_obj,
                          None))

    def test_get_next_xml(self):
        self.assertEquals(util.get_next_xml({'rel': 'next',
                                             'href': 'http://nextlink'}),
                          '<ns0:link xmlns:ns0="http://www.w3.org/2005/Atom" \
href="http://nextlink" rel="next"/>')

    def compare_xml(self, expected, actual):
        expectedObject = objectify.fromstring(expected)
        expected = etree.tostring(expectedObject)
        actualObject = objectify.fromstring(actual)
        actual = etree.tostring(actualObject)
        self.assertEquals(expected, actual)

if __name__ == '__main__':

    # import sys;sys.argv = ['', 'Test.testName']

    unittest.main()
