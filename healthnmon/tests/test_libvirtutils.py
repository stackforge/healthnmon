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
from healthnmon.utils import XMLUtils


class XMLUtilsTest(unittest.TestCase):

    def setUp(self):
        self.utils = XMLUtils()

    def test_parseXML(self):
        self.assertEqual(self.utils.parseXML(
            """<outer><inner a='90'>mytext1</inner>
                      <inner>mytext2</inner>
               </outer>""",
            "//outer/inner"),
            ['mytext1', 'mytext2'])
        self.assertEqual(self.utils.parseXML(
            "<outer><inner>mytext1</inner></outer>", "//outer/inner"),
            'mytext1')

    def test_parseXMLAttributes(self):
        xml = """<outer><inner>mytext1</inner>
                        <inner b='23'>mytext2</inner>
                 </outer>"""
        self.assertEqual(
            self.utils.parseXMLAttributes(xml, '//outer/inner', 'b'), None)
        self.assertEqual(self.utils.parseXMLAttributes(
            xml, '//outer/inner', 'b', True), ['23'])

    def test_getNodeXML(self):
        xml = """<outer><inner>mytext1</inner>
                        <inner b='23'>mytext2</inner>
                        <a><b>88</b><b>87</b></a><b>89</b></outer>"""
        self.assertEquals(
            self.utils.getNodeXML(xml, "//outer/b"), ['<b>89</b>'])
        self.assertEquals(self.utils.getNodeXML(
            xml, "//outer/a/b"), ['<b>88</b>', '<b>87</b>'])

        xml = """<outer xmlns=\"http://namespace\">
                    <inner>mytext1</inner>
                    <inner b='23'>mytext2</inner>
                    <a><b>88</b><b>87</b></a><b>89</b>
                </outer>"""
        namespaces = {'a': 'http://namespace'}
        self.assertEquals(self.utils.getNodeXML(xml,
                                                "//a:outer/a:b",
                                                namespaces),
                          ['<b xmlns="http://namespace">89</b>'])
        self.assertEquals(
            self.utils.getNodeXML(xml, "//a:outer/a:a/a:b", namespaces),
            ['<b xmlns="http://namespace">88</b>',
             '<b xmlns="http://namespace">87</b>'])
