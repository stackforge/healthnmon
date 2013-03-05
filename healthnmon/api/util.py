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

import os
import StringIO

from xml.dom.minidom import parseString
from xml.dom.minidom import Node
from lxml import etree
from lxml.etree import Element
from lxml.etree import SubElement
from webob import Response
from nova.openstack.common import cfg
from .. import log as logging
from nova.api.openstack import common
from ..api import constants

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


def get_path_elements(path_str):
    """ Get path tokens of an absolute path of
        an XML element. This also considers
        the string between '[' and ']' along with
        '/' as separator.
        :returns: each token one at a time.
    """

    L = path_str.rsplit('/')
    for word in L:
        if '[' in word:
            k = word.split('[')
            yield k[0]
            for num in k[1::]:
                # XPath is indexed at 1
                yield (int(num[0:len(num) - 1]) - 1)
        else:
            yield word


def xml_to_dict(xml_str):
    """ Convert xml to a dict object
        :param xml_str: well-formed xml string
        :returns: simple dict object containing xml as key-value pairs.
    """
    xml_str = xml_str.replace('\n', '')
    xml_str = xml_str.replace('\r', '')
    doc = parseString(xml_str)
    unlink_whitespace(doc.documentElement)
    return element_to_dict(doc.documentElement)


def element_to_dict(parent):
    """ Convert dom element to dictionary
        :param parent: parent dom element
        :returns: dict object for the dom element
    """
    def _get_links_dict(element):
        href = element.getAttribute('href')
        rel = element.getAttribute('rel')
        return {
            'href': href,
            'rel': rel,
        }

    def _get_member_dict(element):
        named_map = element.attributes
        d = {}
        for i in xrange(0, len(named_map)):
            name = named_map.item(i).name
            if str(name).startswith('xmlns'):
                continue
            d[named_map.item(i).localName] = named_map.item(i).value
        child_dict = element_to_dict(element)
        if child_dict is not None:
            d.update(child_dict)
        else:
            d.update({'links': []})
        return d

    child = parent.firstChild
    if not child:
        return None
    elif child.nodeType == Node.TEXT_NODE:
        return child.nodeValue
    d = {}
    while child is not None:
        if child.nodeType == Node.ELEMENT_NODE:
            try:
                # We are hard coding here as atom:link is hard coded elsewhere
                # and there is no one particular standard to convert to json
                # when xml namespaces are involved. The other reason is to
                # be consistent with openstack responses.
                # NOTE(Siva): As a resultant of the above, if there is a
                # child xml element with name 'links'
                # that would get added to the links dictionaries.
                if child.tagName == 'atom:link':
                    child.tagName = 'links'
                elif child.tagName in constants.MEMBER_MAP:
                    child.tagName = constants.MEMBER_MAP[child.tagName]
                d[child.tagName]
            except KeyError:
                if child.tagName == 'links':
                    d[child.tagName] = [_get_links_dict(child)]
                elif child.tagName in constants.MEMBER_MAP.values():
                    d[child.tagName] = [_get_member_dict(child)]
                else:
                    d[child.tagName] = element_to_dict(child)
                child = child.nextSibling
                continue
            if not isinstance(d[child.tagName], list):
                first_element = d[child.tagName]
                d[child.tagName] = [first_element]
            if child.tagName == 'links':
                d[child.tagName].append(_get_links_dict(child))
            elif child.tagName in constants.MEMBER_MAP.values():
                d[child.tagName].append(_get_member_dict(child))
            else:
                d[child.tagName].append(element_to_dict(child))
        child = child.nextSibling
    return d


def unlink_whitespace(node, unlink=True):
    """ Unlink whitespace nodes from the dom element """

    remove_list = []
    for child in node.childNodes:
        if child.nodeType == Node.TEXT_NODE and not child.data.strip():
            remove_list.append(child)
        elif child.hasChildNodes():
            unlink_whitespace(child, unlink)
    for node in remove_list:
        node.parentNode.removeChild(node)
        if unlink:
            node.unlink()


def replace_with_links(xml_str, tag_dict_list, replace_dict_out):
    """ Replace entity nodes in input xml with entity references.
        tag_dict_list should contain tag dictionaries; each dict should
        contain the following keys:
        tag: element tag name
        tag_replacement : replacement tag in output xml, same as input tag
                          if None.
        tag_key: Key element tag, if entity does not contain any child
                 elements, this would be added as attribute with value as
                 element text.
        tag_attrib: list of child element tags that are used as attributes
                    in the replaced entity reference.
        tag_collection_url: collection url to be used for creation
                    of the link.
        If the child is an element containing only a single text node
        and tag_key is null, it's data is taken as the tag_key.
        :param xml_str: input xml with no default namespace prefixes
        :param tag_dict_list: list of tag dictionaries
        :param replace_dict_out: the xpath of elements replaced are put in the
                out parameter dict
        :returns: output xml containing entity references
        :raises TagDictionaryError: if resource references cannot be
        constructed using the given tag dictionary.
    """

    def _validate_tag_dict(tag_dict):
        if not tag_dict:
            return False
        try:
            tag_dict['tag']
            tag_dict['tag_key']
            tag_dict['tag_replacement']
            tag_dict['tag_attrib']
            tag_dict['tag_collection_url']
        except KeyError:
            return False
        return True

    def _get_tag_dict_values(tag_dict):
        return (tag_dict['tag'], tag_dict['tag_key'],
                tag_dict['tag_replacement'], tag_dict['tag_attrib'],
                tag_dict['tag_collection_url'])

    if not tag_dict_list:
        return xml_str

#    if (not replace_dict_out):
#        replace_dict_out = {}

    tree = etree.parse(StringIO.StringIO(xml_str),
                       etree.XMLParser(remove_blank_text=True))
    root = tree.getroot()
    rootNS = ''
    if not root.prefix and root.nsmap:
        rootNS = root.nsmap[None]
    elif root.nsmap and root.prefix is not None:
        rootNS = root.nsmap[root.prefix]
    ROOTNS = '{%s}' % rootNS
    for tag_dict in tag_dict_list:
        if _validate_tag_dict(tag_dict):
            try:
                (tag, tag_key, tag_replacement, tag_attrib_list,
                 tag_collection_url) = _get_tag_dict_values(tag_dict)
                elements_to_be_replaced = []
                for element in root.iter(ROOTNS + str(tag)):
                    nsmap = {'atom': constants.XMLNS_ATOM}
                    out_dict = {}
                    if not tag_replacement:
                        tag_replacement = tag
                    replace_element = Element(ROOTNS + tag_replacement,
                                              nsmap=nsmap)
                    if tag_attrib_list is not None:
                        for tag in tag_attrib_list:
                            if element.find(tag) is not None:
                                replace_element.attrib[ROOTNS + tag] = \
                                    element.find(tag).text
                                out_dict[tag] = element.find(tag).text
                    resource_key = None
                    if not tag_key or len(element) == 0:
                        resource_key = element.text
                    elif tag_key is not None and element.find(
                            ROOTNS + tag_key) is not None and \
                            element.find(ROOTNS + tag_key).text is not None:

                        resource_key = element.find(ROOTNS
                                                    + tag_key).text
                    if not resource_key:
                        raise TagDictionaryError(
                            'No resource key found from tag dictionary:',
                            tag_dict)
                    if tag_key is not None:
                        replace_element.attrib[ROOTNS + tag_key] = \
                            resource_key
                        out_dict[tag_key] = resource_key

                    href = os.path.join(tag_collection_url,
                                        str(resource_key))
                    bookmark = \
                        os.path.join(
                            common.remove_version_from_href(
                                tag_collection_url),
                            str(resource_key))
                    links = [{'rel': 'self', 'href': href},
                             {'rel': 'bookmark', 'href': bookmark}]

                    for link_dict in links:
                        SubElement(replace_element, constants.ATOM
                                   + 'link', attrib=link_dict)
                    out_dict['links'] = links
                    elements_to_be_replaced.append((element,
                                                    replace_element, out_dict))

                for (element, replace_element, out_dict) in \
                        elements_to_be_replaced:
                    if element.getparent() is None:
                        tree._setroot(replace_element)
                    else:
                        element.getparent().replace(element,
                                                    replace_element)

                for (element, replace_element, out_dict) in \
                        elements_to_be_replaced:
                    LOG.debug(_('Replaced element path: %s'
                                % replace_element.getroottree().getpath(
                                    replace_element)))
                    replace_dict_out.update(
                        {tree.getpath(replace_element): out_dict})
            except (KeyError, IndexError, ValueError), err:
                LOG.error(_('Lookup Error while finding tag \
                healthnmon api... %s ' % str(err)), exc_info=1)
    return etree.tostringlist(tree.getroot())[0]


def dump_resource_xml(resource_obj, tag):
    """Serialize object using resource model """

    LOG.debug(_('Exporting tag: %s as xml...' % tag))
    xml_out_file = StringIO.StringIO()
    resource_obj.export(xml_out_file, 0, name_=tag)
    return xml_out_file.getvalue()


def get_project_context(req):
    """ Get project context from request
    :param req: request object from which context would be fetched.
    :returns: project context tuple (context, project_id)
    """
    context = None
    project_id = ''
    try:
        context = req.environ['nova.context']
        project_id = context.project_id
    except KeyError, err:
        LOG.error(_('Exception while fetching nova context from request... %s '
                    % str(err)), exc_info=1)
    return (context, project_id)


def get_content_accept_type(req):
    """ Returns either xml or json depending on the type
        specified in http request path or in the accept header of the
        request.
        The content type specified in the request path takes
        priority.
    """

    def is_path_accept(req, data_type):
        """ Returns True if the request path ends with the specified
            data type
        """

        if str(req.path_info).endswith('.' + data_type):
            return True
        else:
            return False

    def is_header_accept(req, content_type):
        """ Returns True if the content_type matches any of the accept headers
            specified in the request
        """

        for header in list(req.accept):
            try:
                str(header).index(content_type)
            except ValueError:
                continue
            return True
        return False

    if is_path_accept(req, 'json'):
        return 'json'
    elif is_path_accept(req, 'xml'):
        return 'xml'
    elif is_header_accept(req, 'xml'):
        return 'xml'
    elif is_header_accept(req, 'json'):
        return 'json'


def create_response(content_type, body):
    """ Prepare a response object
        with the set content type

        :param content_type: content type to be specified in the header
        :param body: response body
        :returns: returns the prepared response object.
    """

    resp = Response(content_type=content_type)
    resp.body = body
    return resp


def update_dict_using_xpath(input_dict, xpath_dict):
    """ Update an input dict with values from xpath_dict
        by traversing the xpath in the dict.
        if dict cannot be traversed for a particular xpath key,
        the xpath key is ignored.

        :params input_dict: input dict to be traversed and updated.
        :params xpath_dict: dict containing xpath as key, value is the value
                            to be replaced with for the traversed xpath in
                            the input dict.
    """

    if not input_dict:
        return None
    if not xpath_dict:
        return input_dict
    for (k, d) in xpath_dict.items():
        try:
            loc = input_dict
            if k.startswith('/'):
                k = k[1::]
            path_elements = []
            for ele in get_path_elements(k):
                path_elements.append(ele)
            for i in range(len(path_elements) - 1):
                loc = loc[path_elements[i]]
            loc[path_elements[-1]]
            loc[path_elements[-1]] = d
        except (LookupError, ValueError), err:
            LOG.debug(_('XPath traversion error in input \
            dictionary current key:%s ' % str(err)))
    return input_dict


def get_entity_list_xml(
    entity_dict,
    nsmap,
    root_element_tag,
    sub_element_tag,
    root_prefix='None',
):
    """ Get entity list in xml format
        :params: entity_dict with root key as entity name. The value is
        an array of entity dictionaries which each containing entity attributes
        as keys and a separate 'links' key/value pair. The value of which is an
        array of dictionaries containing hyperlinks with relations to the
        entity in each dictionary. An example entity_dict is shown below:
        entity_dict = {
        'vmhosts': [{
            "id": 'host-1234',
            "name": 'newhost',
            "links": [
                {
                    "rel": "self",
                    "href": 'http://localhost:8774/v2/admin/vmhosts'
                },
                {
                    "rel": "bookmark",
                    "href": 'http://localhost:8774/admin/vmhosts'
                }
             ],
        }],
        "vmhosts_links": [
                {
                    "rel": "next",
                    "href": 'http://localhost:8774/v2/admin/vmhosts&marker=4"
                }
        ]}
        :params nsmap: namespace map to be used for the generated xml.
        :params root_element_tag: element tag of the root element.
        :params sub_element_tag: element tag for each sub element. i.e for each
        entity dictionary.
        :params root_prefix: root prefix to be used for identifying the
        namespace of the document from the nsmap.
        :returns: list of entities in xml format using the entity dictionary.
        :raises LookupError: If there is more than one root(key) element in the
        entity_dict.
    """
    if not entity_dict:
        return ''
    # TODO(siva): add check for entities_links
    keys = entity_dict.keys()
    root_key = ''
    if len(keys) > 2:
        raise LookupError('More than one root element in entity')
    page_links = []
    if len(keys) == 2:
        if keys[0].endswith("_links"):
            page_links = entity_dict[keys[0]]
            root_key = keys[1]
        elif keys[1].endswith("_links"):
            root_key = keys[0]
            page_links = entity_dict[keys[1]]
        else:
            raise LookupError('More than one root element in entity')
    else:
        root_key = entity_dict.keys()[0]
    root_namespace = ''
    if nsmap is not None and root_prefix in nsmap:
        root_namespace = '{%s}' % nsmap[root_prefix]
    root = Element(root_namespace + root_element_tag, nsmap=nsmap)
    dict_list = entity_dict[root_key]
    for ent in dict_list:
        if not ent:
            continue
        link_list = []
        if 'links' in ent:
            link_list = ent['links']
            del ent['links']
        attrib = {}
        for (key, val) in ent.items():
            if key is not None:
                if val is not None:
                    attrib[key] = val
                else:
                    attrib[key] = ''
        entity_sub = SubElement(root, root_namespace + sub_element_tag,
                                attrib)
        for link in link_list:
            SubElement(entity_sub, constants.ATOM + 'link', link)

    for link in page_links:
        SubElement(root, constants.ATOM + 'link', link)
    return etree.tostringlist(root)[0]


class TagDictionaryError(Exception):

    """ Error thrown when an invalid tag dictionary
        is provided.
    """

    def __init__(self, msg, tag_dict=None):
        Exception.__init__(self)
        self.msg = msg
        self.tag_dict = tag_dict

    def __str__(self):
        return self.msg + str(self.tag_dict)


def get_next_xml(attrib):
    ''' Get atom link with given attributes dict '''
    return etree.tostring(Element(constants.ATOM + 'link', attrib=attrib))


def set_select_attributes(resource_obj, attr_dict):
    ''' Set select attributes on the object
        :param resource_obj: object on which attributes are to be set
        :param attr_dict: attribute key value pairs to be set on the object
        :returns: resource object with attribute values set
    '''
    if not attr_dict:
        return resource_obj
    for (key, val) in attr_dict.items():
        setattr(resource_obj, key, val)
    return resource_obj


def serialize_simple_obj(py_obj, root_tag, var_names):
    """
        serializes simple object to xml
        :param py_obj: simple python object
        :param root_tag: root tag to be used
        :param var_names: names of member attributes to be retrieved from
        the object
        :returns: xml with child member elements value pairs from var_names
    """

    getstr = lambda obj: ('' if not obj else str(obj))
    root = etree.Element(root_tag)
    for var in var_names:
        child = etree.SubElement(root, var)
        try:
            value = getattr(py_obj, var)
        except AttributeError:
            continue
        else:
            child.text = getstr(value)
    return etree.tostring(root)


def append_xml_as_child(xml_str, child_xml):
    '''
    Append xml as child to a parent xml string
    :param xml_str: parent xml string
    :param child_xml: child xml string
    :returns: parent xml appended with child xml.
    '''
    root = etree.fromstring(xml_str,
                            parser=etree.XMLParser(remove_blank_text=True))
    child = etree.fromstring(child_xml,
                             parser=etree.XMLParser(remove_blank_text=True))
    root.append(child)
    return etree.tostring(root)


def get_query_fields(req):
    ''' Get list of query fields from the webob request '''
    if constants.QUERY_FIELD_KEY in req.GET:
        return sum(map(lambda x: ([] if not x else str(x).split(',')),
                   req.GET.getall(constants.QUERY_FIELD_KEY)), [])
    else:
        return None


def get_select_elements_xml(input_xml, field_list, default_field=None):
    ''' Get select element xml from input xml. Invalid field names are
        ignored. If a default field is specified and if it is not in the
        field_list it will be added on top of selected elements.
        :param input_xml: input xml
        :param field_list: element names as a list
        :returns: select elements as separate xml
    '''
    root = etree.fromstring(input_xml)
    root_namespace = ''
    if not root.prefix and root.nsmap:
        root_namespace = root.nsmap[None]
    elif root.nsmap and root.prefix is not None:
        root_namespace = root.nsmap[root.prefix]
    root_ns = '{%s}' % root_namespace
    display_root = etree.Element(root.tag, nsmap=root.nsmap)
    for field in field_list:
        try:
            for ele in root.findall(root_ns + field):
                display_root.append(ele)
        except:
            # Ignore if the field name is invalid.
            pass
    if len(display_root) > 0 and default_field and  \
            default_field not in field_list:
        try:
            for i, ele in enumerate(root.findall(root_ns + default_field)):
                display_root.insert(i, ele)
        except:
            # Ignore if the field name is invalid.
            pass
    return etree.tostring(display_root)
